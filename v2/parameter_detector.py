"""
Semantic Parameter Detector v2.0

Detects parameters in prompts using embedding-based semantic similarity
instead of regex pattern matching.
"""

import re
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .embedding_manager import EmbeddingManager
from .domain_config_v2 import DomainConfigV2, CONTEXT_PATTERNS, CLASS_KEYWORDS


@dataclass
class EntityContext:
    """Entity extracted from prompt with context"""
    text: str
    label: str  # NER label or "NOUN_CHUNK"
    context: str  # Surrounding text for context-aware embedding
    start: int
    end: int
    context_window: str  # Wider context for parameter detection


@dataclass
class ParameterMatch:
    """Detected parameter with confidence score"""
    parameter: str
    value: str
    confidence: float
    context: str
    method: str  # "semantic", "context", "keyword"


class SemanticParameterDetector:
    """
    Detects parameters using semantic similarity.

    Process:
    1. Extract entities and noun chunks from prompt
    2. For each entity, embed it with context
    3. Compare to parameter anchor embeddings
    4. Return matches above confidence threshold
    """

    # Words that should NEVER be matched as parameters
    INVALID_PARAMETER_VALUES = {
        # Common words
        "something", "anything", "nothing", "everything",
        "someone", "anyone", "everyone", "nobody",
        "somewhere", "anywhere", "everywhere", "nowhere",
        "that", "this", "it", "they", "them", "these", "those",
        "which", "what", "who", "whom", "whose",
        # Verbs/actions
        "book", "booking", "travel", "traveling", "fly", "flying",
        "need", "want", "like", "prefer", "would",
        # Generic nouns
        "flight", "flights", "ticket", "tickets", "trip", "journey",
        "cost", "price", "budget", "fare",
        "time", "timing", "preference", "option",
        # Pronouns
        "i", "me", "my", "we", "us", "our", "you", "your",
        # Adjectives
        "comfortable", "cheap", "expensive", "good", "best", "nice",
        # Time words (not specific)
        "later", "soon", "early", "late",
    }

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        domain: DomainConfigV2,
        nlp=None
    ):
        """
        Initialize detector.

        Args:
            embedding_manager: Pre-configured embedding manager
            domain: Domain configuration
            nlp: spaCy model (loaded if not provided)
        """
        self.embeddings = embedding_manager
        self.domain = domain

        if nlp is None:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        else:
            self.nlp = nlp

        # Ensure anchors are pre-computed
        if not self.embeddings._anchor_embeddings:
            self.embeddings.precompute_anchors(domain.parameter_anchors)

    def detect(self, prompt: str) -> Dict[str, ParameterMatch]:
        """
        Detect all parameters in a prompt.

        Args:
            prompt: Input prompt text

        Returns:
            Dict mapping parameter names to ParameterMatch objects
        """
        # Step 1: Extract entities with context
        entities = self._extract_entities(prompt)

        # Step 2: Detect class explicitly (keyword matching)
        results = {}
        used_values = set()  # Track values to prevent duplicates

        class_match = self._detect_class(prompt)
        if class_match:
            results["class"] = class_match

        # Step 3: Direct type-based matching for dates, times, budgets
        # These work better with entity type than semantic similarity
        type_matches = self._match_by_entity_type(entities)
        for param, match in type_matches.items():
            if param not in results:
                results[param] = match

        # Step 4: Match entities to parameters using semantic similarity
        semantic_matches = self._match_semantically(entities, prompt)

        # Step 5: Use context patterns as fallback/confirmation for locations
        context_matches = self._match_by_context(entities, prompt)

        # Step 6: Merge results (prefer semantic matches, use context as confirmation)
        for param, match in semantic_matches.items():
            if param not in results:
                # Check if value is already used (except for non-exclusive params)
                if param in ["origin", "destination"] and match.value in used_values:
                    continue

                # Check if context also supports this match
                if param in context_matches and context_matches[param].value == match.value:
                    # Boost confidence if both methods agree on same value
                    match.confidence = min(1.0, match.confidence + 0.1)

                results[param] = match
                if param in ["origin", "destination"]:
                    used_values.add(match.value)

        # Add context-only matches for parameters not found semantically
        # Only for location parameters
        for param, match in context_matches.items():
            if param not in results and param in ["origin", "destination"]:
                if match.value in used_values:
                    continue
                if match.confidence >= 0.6:
                    results[param] = match
                    used_values.add(match.value)

        return results

    def _match_by_entity_type(self, entities: List[EntityContext]) -> Dict[str, ParameterMatch]:
        """
        Match entities to parameters based on their NER type.
        Best for dates, times, and money amounts.
        """
        results = {}

        for entity in entities:
            # Skip invalid values
            if entity.text.lower().strip() in self.INVALID_PARAMETER_VALUES:
                continue

            # Date entities -> date_outbound
            if entity.label in ["DATE", "DATE_TIME"] and "date_outbound" not in results:
                # Check if it looks like a date (not just "soon" or "later")
                text_lower = entity.text.lower()
                if any(m in text_lower for m in ["jan", "feb", "mar", "apr", "may", "jun",
                                                   "jul", "aug", "sep", "oct", "nov", "dec",
                                                   "monday", "tuesday", "wednesday", "thursday",
                                                   "friday", "saturday", "sunday", "next", "/"]):
                    results["date_outbound"] = ParameterMatch(
                        parameter="date_outbound",
                        value=entity.text,
                        confidence=0.85,
                        context=entity.context_window,
                        method="entity_type"
                    )

            # Time entities -> time_preference
            if entity.label == "TIME" and "time_preference" not in results:
                results["time_preference"] = ParameterMatch(
                    parameter="time_preference",
                    value=entity.text,
                    confidence=0.85,
                    context=entity.context_window,
                    method="entity_type"
                )

            # Money entities -> budget
            if entity.label == "MONEY" and "budget" not in results:
                results["budget"] = ParameterMatch(
                    parameter="budget",
                    value=entity.text,
                    confidence=0.85,
                    context=entity.context_window,
                    method="entity_type"
                )

        return results

    def _extract_entities(self, prompt: str) -> List[EntityContext]:
        """Extract entities and noun chunks with context"""
        doc = self.nlp(prompt)
        entities = []
        seen_spans = set()

        # Extract named entities
        for ent in doc.ents:
            span_key = (ent.start_char, ent.end_char)
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)

            # Get context windows
            token_start = max(0, ent.start - 3)
            token_end = min(len(doc), ent.end + 3)
            narrow_context = doc[token_start:token_end].text

            wider_start = max(0, ent.start - 6)
            wider_end = min(len(doc), ent.end + 6)
            wider_context = doc[wider_start:wider_end].text

            entities.append(EntityContext(
                text=ent.text,
                label=ent.label_,
                context=narrow_context,
                start=ent.start_char,
                end=ent.end_char,
                context_window=wider_context
            ))

        # Extract noun chunks not covered by NER
        for chunk in doc.noun_chunks:
            # Skip if overlaps with existing entity
            overlaps = any(
                not (chunk.end_char <= e.start or chunk.start_char >= e.end)
                for e in entities
            )
            if overlaps:
                continue

            # Skip common non-informative chunks
            if chunk.text.lower() in ["i", "me", "you", "we", "it", "flight", "ticket", "tickets"]:
                continue

            token_start = max(0, chunk.start - 3)
            token_end = min(len(doc), chunk.end + 3)
            context = doc[token_start:token_end].text

            wider_start = max(0, chunk.start - 6)
            wider_end = min(len(doc), chunk.end + 6)
            wider_context = doc[wider_start:wider_end].text

            entities.append(EntityContext(
                text=chunk.text,
                label="NOUN_CHUNK",
                context=context,
                start=chunk.start_char,
                end=chunk.end_char,
                context_window=wider_context
            ))

        # Also extract potential date/time patterns not caught by NER
        date_patterns = [
            r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d{4})?)\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(next\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b',
            r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))\b',
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, prompt, re.IGNORECASE):
                span_key = (match.start(), match.end())
                if span_key in seen_spans:
                    continue

                # Check if overlaps with existing
                overlaps = any(
                    not (match.end() <= e.start or match.start() >= e.end)
                    for e in entities
                )
                if overlaps:
                    continue

                seen_spans.add(span_key)

                # Get context
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(prompt), match.end() + 20)
                context = prompt[start_pos:end_pos]

                entities.append(EntityContext(
                    text=match.group(1),
                    label="DATE_TIME",
                    context=context,
                    start=match.start(),
                    end=match.end(),
                    context_window=context
                ))

        # Extract budget patterns
        budget_patterns = [
            r'(\d+k?\s*(?:rupees|rs|inr|Rs\.?))',
            r'((?:Rs\.?|₹)\s*\d+k?)',
            r'(\d+k?)\s*(?:budget|cost|price|fare)',
        ]

        for pattern in budget_patterns:
            for match in re.finditer(pattern, prompt, re.IGNORECASE):
                span_key = (match.start(), match.end())
                if span_key in seen_spans:
                    continue

                overlaps = any(
                    not (match.end() <= e.start or match.start() >= e.end)
                    for e in entities
                )
                if overlaps:
                    continue

                seen_spans.add(span_key)

                start_pos = max(0, match.start() - 20)
                end_pos = min(len(prompt), match.end() + 20)
                context = prompt[start_pos:end_pos]

                entities.append(EntityContext(
                    text=match.group(0),
                    label="MONEY",
                    context=context,
                    start=match.start(),
                    end=match.end(),
                    context_window=context
                ))

        return entities

    def _is_valid_parameter_value(self, value: str, param_name: str) -> bool:
        """Check if a value is valid for the given parameter"""
        value_lower = value.lower().strip()

        # Reject values in invalid list
        if value_lower in self.INVALID_PARAMETER_VALUES:
            return False

        # Reject very short values (likely fragments)
        if len(value_lower) <= 2:
            return False

        # For location parameters, require capitalization (proper nouns)
        if param_name in ["origin", "destination"]:
            if not value[0].isupper():
                return False

        return True

    def _match_semantically(
        self,
        entities: List[EntityContext],
        prompt: str
    ) -> Dict[str, ParameterMatch]:
        """Match entities to parameters using semantic similarity"""
        results = {}
        used_values = set()  # Track values to prevent duplicates

        # Sort entities by likely importance (longer text first, then by position)
        sorted_entities = sorted(entities, key=lambda e: (-len(e.text), e.start))

        for entity in sorted_entities:
            # Skip entities that don't make sense for any parameter
            if entity.label in ["PERSON", "WORK_OF_ART", "LAW"]:
                continue

            # Skip invalid parameter values
            entity_text_lower = entity.text.lower().strip()
            if entity_text_lower in self.INVALID_PARAMETER_VALUES:
                continue

            # Embed entity with its context
            entity_with_context = f"{entity.context}"
            entity_embedding = self.embeddings.encode(entity_with_context)

            # Compare to each parameter's anchors
            best_param = None
            best_score = 0.0

            for param_name, anchor_embeddings in self.embeddings._anchor_embeddings.items():
                # Skip if this parameter already has a match
                if param_name in results:
                    continue

                # Check if entity type is compatible with this parameter
                allowed_types = self.domain.entity_type_mapping.get(param_name, [])
                if allowed_types and entity.label not in allowed_types and entity.label != "NOUN_CHUNK" and entity.label != "DATE_TIME":
                    continue

                # For origin/destination, prevent using same value
                if param_name in ["origin", "destination"]:
                    if entity.text in used_values:
                        continue
                    if not self._is_valid_parameter_value(entity.text, param_name):
                        continue

                # Compute max similarity to any anchor
                similarities = self.embeddings.cosine_similarity_batch(
                    entity_embedding,
                    anchor_embeddings
                )
                max_sim = float(np.max(similarities))

                # Use higher threshold for location params to reduce false positives
                effective_threshold = self.domain.confidence_threshold
                if param_name in ["origin", "destination"]:
                    effective_threshold = max(0.65, effective_threshold)

                if max_sim > best_score and max_sim >= effective_threshold:
                    best_score = max_sim
                    best_param = param_name

            # Accept if found a valid match
            if best_param and best_score >= self.domain.confidence_threshold:
                results[best_param] = ParameterMatch(
                    parameter=best_param,
                    value=entity.text,
                    confidence=best_score,
                    context=entity.context_window,
                    method="semantic"
                )
                # Track used values to prevent duplicates
                if best_param in ["origin", "destination"]:
                    used_values.add(entity.text)

        return results

    def _match_by_context(
        self,
        entities: List[EntityContext],
        prompt: str
    ) -> Dict[str, ParameterMatch]:
        """Match entities to parameters using context word patterns"""
        results = {}
        used_values = set()

        for entity in entities:
            # Skip invalid values
            if entity.text.lower().strip() in self.INVALID_PARAMETER_VALUES:
                continue

            context_lower = entity.context_window.lower()

            for param_name, patterns in CONTEXT_PATTERNS.items():
                # Skip if already matched
                if param_name in results:
                    continue

                # Validate for location params
                if param_name in ["origin", "destination"]:
                    if not self._is_valid_parameter_value(entity.text, param_name):
                        continue
                    if entity.text in used_values:
                        continue

                for pattern in patterns:
                    # Check if pattern appears near entity
                    if pattern in context_lower:
                        # Calculate confidence based on proximity
                        pattern_pos = context_lower.find(pattern)
                        entity_pos = context_lower.find(entity.text.lower())

                        if pattern_pos != -1 and entity_pos != -1:
                            distance = abs(pattern_pos - entity_pos)
                            # Closer = higher confidence
                            confidence = max(0.5, 0.8 - (distance / 50))

                            # Higher threshold for location params
                            min_confidence = 0.6 if param_name in ["origin", "destination"] else 0.5
                            if confidence >= min_confidence:
                                results[param_name] = ParameterMatch(
                                    parameter=param_name,
                                    value=entity.text,
                                    confidence=confidence,
                                    context=entity.context_window,
                                    method="context"
                                )
                                if param_name in ["origin", "destination"]:
                                    used_values.add(entity.text)
                            break

        return results

    def _detect_class(self, prompt: str) -> Optional[ParameterMatch]:
        """Detect flight class using keyword matching"""
        prompt_lower = prompt.lower()

        for class_name, keywords in CLASS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    # Find position for context
                    pos = prompt_lower.find(keyword)
                    start = max(0, pos - 20)
                    end = min(len(prompt), pos + len(keyword) + 20)
                    context = prompt[start:end]

                    return ParameterMatch(
                        parameter="class",
                        value=class_name,
                        confidence=0.95,  # High confidence for exact keyword match
                        context=context,
                        method="keyword"
                    )

        return None

    def get_missing_parameters(
        self,
        detected: Dict[str, ParameterMatch]
    ) -> List[str]:
        """Get list of parameters not detected"""
        all_params = set(self.domain.parameter_anchors.keys())
        detected_params = set(detected.keys())

        # date_return is optional, don't count as missing unless explicit return mentioned
        optional = {"date_return"}
        required = all_params - optional

        return list(required - detected_params)
