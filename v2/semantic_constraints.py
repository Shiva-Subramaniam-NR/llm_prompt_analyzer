"""
Semantic Constraint Detector v2.0

Detects constraints in prompts using semantic similarity instead of regex patterns.

Constraint Types:
- Hard Constraints: Must/must not (e.g., "must depart before 10am")
- Soft Preferences: Prefer/ideally (e.g., "preferably business class")
- Flexible/No Preference: Any/doesn't matter (e.g., "timing doesn't matter")

Key Advantage: Understands semantic variations without hardcoded patterns:
- "It's essential to depart before 10am" → hard time constraint
- "I'd really like a morning flight" → soft time preference
- "Not picky about timing" → flexible on time
"""

import re
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .embedding_manager import EmbeddingManager


# ============================================================
# CONSTRAINT TYPES
# ============================================================

class ConstraintType(Enum):
    """Types of constraints users can express"""
    HARD_CONSTRAINT = "hard_constraint"      # Must/must not
    SOFT_PREFERENCE = "soft_preference"      # Prefer/would like
    FLEXIBLE = "flexible"                    # Any/doesn't matter
    REQUIREMENT = "requirement"              # Need/require
    PROHIBITION = "prohibition"              # Cannot/should not
    IDEAL = "ideal"                          # Ideally/best if


class ConstraintStrength(Enum):
    """Strength of constraint (for scoring)"""
    MANDATORY = 1.0      # Must comply (hard constraints, prohibitions)
    STRONG = 0.8         # Should comply (requirements, ideals)
    MODERATE = 0.5       # Nice to have (soft preferences)
    WEAK = 0.3           # Very flexible (loose preferences)
    NONE = 0.0           # No constraint (flexible/any)


@dataclass
class Constraint:
    """
    Represents a detected constraint in the prompt.
    """
    parameter: str                   # Which parameter (time, class, budget, etc.)
    type: ConstraintType             # Type of constraint
    strength: ConstraintStrength     # How strong is this constraint
    text: str                        # Original text expressing the constraint
    value: Optional[str] = None      # Specific value if mentioned (e.g., "10am", "business")
    context: str = ""                # Surrounding context
    confidence: float = 0.0          # Detection confidence (0-1)
    method: str = "semantic"         # Detection method

    def __str__(self) -> str:
        return f"{self.type.value}({self.parameter}): '{self.text}' [strength={self.strength.value:.1f}]"


# ============================================================
# SEMANTIC CONSTRAINT DETECTOR
# ============================================================

class SemanticConstraintDetector:
    """
    Detects constraints using semantic similarity to anchor phrases.

    Replaces regex patterns with embedding-based understanding.
    Can detect constraint expressions even with creative phrasing.

    Example:
        detector = SemanticConstraintDetector(embedding_manager)
        constraints = detector.detect("I really must depart before 10am")
        # Returns: hard_constraint(time): "must depart before 10am"
    """

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        similarity_threshold: float = 0.45
    ):
        """
        Initialize detector.

        Args:
            embedding_manager: Pre-configured embedding manager
            similarity_threshold: Minimum similarity for constraint detection
        """
        self.embeddings = embedding_manager
        self.threshold = similarity_threshold

        # Load constraint type definitions
        self.constraint_definitions = self._load_constraint_definitions()

        # Pre-compute anchor embeddings
        self._precompute_constraint_embeddings()

        # Initialize spaCy for sentence segmentation
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("[WARN] spaCy not loaded, will use simple sentence splitting")
            self.nlp = None

        print(f"[OK] SemanticConstraintDetector initialized with {len(self.constraint_definitions)} constraint types")

    def _load_constraint_definitions(self) -> Dict[ConstraintType, Dict]:
        """
        Load semantic anchor phrases for each constraint type.

        Returns:
            Dict mapping ConstraintType to definition with anchors
        """
        return {
            ConstraintType.HARD_CONSTRAINT: {
                "anchors": [
                    "must depart before",
                    "must arrive by",
                    "has to leave before",
                    "absolutely must depart",
                    "required to depart before",
                    "essential to arrive by",
                    "necessary to depart before",
                    "it is mandatory to depart",
                    "critical that I depart",
                    "absolutely have to depart",
                    "cannot proceed unless depart",
                    "strictly must depart"
                ],
                "strength": ConstraintStrength.MANDATORY,
                "description": "Absolute requirements (must/must not)"
            },

            ConstraintType.PROHIBITION: {
                "anchors": [
                    "must not be",
                    "cannot be",
                    "should not be",
                    "do not want",
                    "not allowed to",
                    "won't accept",
                    "absolutely not",
                    "under no circumstances",
                    "definitely not",
                    "avoid at all costs"
                ],
                "strength": ConstraintStrength.MANDATORY,
                "description": "Hard prohibitions (cannot/must not)"
            },

            ConstraintType.REQUIREMENT: {
                "anchors": [
                    "need to",
                    "require",
                    "looking for",
                    "want to",
                    "would need",
                    "it should",
                    "expecting",
                    "supposed to be",
                    "ought to be",
                    "have to be"
                ],
                "strength": ConstraintStrength.STRONG,
                "description": "Strong requirements (need/require)"
            },

            ConstraintType.SOFT_PREFERENCE: {
                "anchors": [
                    "prefer morning flight",
                    "would like business class",
                    "hoping for early departure",
                    "if possible prefer",
                    "better if economy class",
                    "wish to fly in morning",
                    "rather have morning flight",
                    "inclined towards business",
                    "leaning towards early flight",
                    "my preference is morning",
                    "would prefer to depart",
                    "ideally prefer morning"
                ],
                "strength": ConstraintStrength.MODERATE,
                "description": "Soft preferences (prefer/would like)"
            },

            ConstraintType.IDEAL: {
                "anchors": [
                    "ideally",
                    "best would be",
                    "perfect would be",
                    "in an ideal world",
                    "optimally",
                    "my first choice",
                    "top preference",
                    "dream scenario",
                    "would be great if",
                    "hoping it could be"
                ],
                "strength": ConstraintStrength.STRONG,
                "description": "Ideal scenarios (ideally/best if)"
            },

            ConstraintType.FLEXIBLE: {
                "anchors": [
                    "timing doesn't matter",
                    "any time is fine",
                    "no preference on class",
                    "flexible about timing",
                    "open to any class",
                    "not particular about time",
                    "whatever timing works",
                    "not picky about class",
                    "don't care about timing",
                    "either morning or evening okay",
                    "any class is fine",
                    "timing is flexible"
                ],
                "strength": ConstraintStrength.NONE,
                "description": "Flexibility/no constraint (any/doesn't matter)"
            }
        }

    def _precompute_constraint_embeddings(self):
        """Pre-compute embeddings for constraint type anchors"""
        print("[INFO] Pre-computing constraint anchor embeddings...")

        constraint_anchors = {}
        for constraint_type, definition in self.constraint_definitions.items():
            constraint_anchors[constraint_type.value] = definition["anchors"]

        self.embeddings.precompute_anchors(constraint_anchors)
        print(f"[OK] Pre-computed anchors for {len(constraint_anchors)} constraint types")

    def detect(self, prompt: str) -> List[Constraint]:
        """
        Detect all constraints in a prompt.

        Args:
            prompt: Input prompt text

        Returns:
            List of detected Constraint objects
        """
        constraints = []

        # Step 1: Segment prompt into clauses/sentences
        segments = self._segment_prompt(prompt)

        # Step 2: For each segment, detect constraint type
        for segment in segments:
            segment_constraints = self._detect_in_segment(segment, prompt)
            constraints.extend(segment_constraints)

        # Step 3: Extract specific values for constraints
        constraints = self._extract_constraint_values(constraints, prompt)

        # Step 4: Deduplicate and merge overlapping constraints
        constraints = self._deduplicate_constraints(constraints)

        return constraints

    def _segment_prompt(self, prompt: str) -> List[str]:
        """
        Segment prompt into meaningful clauses.

        Returns:
            List of text segments to analyze
        """
        segments = []

        if self.nlp:
            # Use spaCy for sentence segmentation
            doc = self.nlp(prompt)
            for sent in doc.sents:
                segments.append(sent.text.strip())

                # Also extract sub-clauses (comma-separated)
                parts = sent.text.split(',')
                if len(parts) > 1:
                    for part in parts:
                        if len(part.strip()) > 10:  # Skip very short fragments
                            segments.append(part.strip())
        else:
            # Simple fallback: split by sentence and comma
            for sent in re.split(r'[.!?]', prompt):
                sent = sent.strip()
                if sent:
                    segments.append(sent)
                    # Also add comma-separated parts
                    for part in sent.split(','):
                        part = part.strip()
                        if len(part) > 10:
                            segments.append(part)

        return list(set(segments))  # Deduplicate

    def _detect_in_segment(self, segment: str, full_prompt: str) -> List[Constraint]:
        """
        Detect constraint type in a text segment.

        Args:
            segment: Text segment to analyze
            full_prompt: Full prompt for context

        Returns:
            List of constraints detected in this segment
        """
        constraints = []

        # Embed the segment
        segment_embedding = self.embeddings.encode(segment)

        # Compare to each constraint type's anchors
        best_type = None
        best_score = 0.0

        for constraint_type, definition in self.constraint_definitions.items():
            # Get pre-computed anchor embeddings
            anchor_embeddings = self.embeddings.get_anchor_embeddings(constraint_type.value)

            if anchor_embeddings is None:
                continue

            # Calculate max similarity to any anchor
            similarities = self.embeddings.cosine_similarity_batch(
                segment_embedding,
                anchor_embeddings
            )
            max_similarity = float(np.max(similarities))

            if max_similarity > best_score:
                best_score = max_similarity
                best_type = constraint_type

        # Accept if above threshold
        if best_type and best_score >= self.threshold:
            # Identify which parameter this constraint applies to
            parameter = self._identify_constrained_parameter(segment, full_prompt)

            if parameter:
                constraint = Constraint(
                    parameter=parameter,
                    type=best_type,
                    strength=self.constraint_definitions[best_type]["strength"],
                    text=segment,
                    context=full_prompt,
                    confidence=best_score,
                    method="semantic"
                )
                constraints.append(constraint)

        return constraints

    def _identify_constrained_parameter(self, segment: str, full_prompt: str) -> Optional[str]:
        """
        Identify which parameter a constraint applies to.

        Args:
            segment: Constraint text
            full_prompt: Full prompt for context

        Returns:
            Parameter name (e.g., "time_preference", "class", "budget")
        """
        segment_lower = segment.lower()

        # Parameter keywords
        parameter_keywords = {
            "time_preference": [
                "time", "timing", "morning", "afternoon", "evening", "night",
                "early", "late", "am", "pm", "hour", "o'clock", "depart",
                "before", "after", "by"
            ],
            "class": [
                "class", "cabin", "seat", "seating", "economy", "business",
                "first", "premium", "coach"
            ],
            "budget": [
                "cost", "price", "budget", "spend", "fare", "rupees", "rs",
                "inr", "cheap", "expensive", "affordable", "money"
            ],
            "date_outbound": [
                "date", "day", "when", "monday", "tuesday", "wednesday",
                "thursday", "friday", "saturday", "sunday", "month",
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ],
            "airline": [
                "airline", "carrier", "indigo", "air india", "spicejet",
                "vistara", "jet", "airways"
            ],
            "stops": [
                "stop", "direct", "non-stop", "layover", "connection", "via"
            ],
            "duration": [
                "duration", "length", "hours", "minutes", "quick", "fast", "slow"
            ]
        }

        # Find best matching parameter
        best_param = None
        max_matches = 0

        for param, keywords in parameter_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in segment_lower)
            if matches > max_matches:
                max_matches = matches
                best_param = param

        # If no clear match, try to infer from context
        if not best_param or max_matches == 0:
            # Check if segment contains time expressions
            time_pattern = r'\d{1,2}(?::\d{2})?\s*(?:am|pm)'
            if re.search(time_pattern, segment_lower):
                return "time_preference"

            # Check for price expressions
            price_pattern = r'\d+k?(?:\s*(?:rupees|rs|inr))?'
            if re.search(price_pattern, segment_lower):
                return "budget"

        return best_param

    def _extract_constraint_values(
        self,
        constraints: List[Constraint],
        prompt: str
    ) -> List[Constraint]:
        """
        Extract specific values mentioned in constraints.

        Args:
            constraints: List of detected constraints
            prompt: Full prompt text

        Returns:
            Constraints with extracted values
        """
        for constraint in constraints:
            # Extract based on parameter type
            if constraint.parameter == "time_preference":
                constraint.value = self._extract_time_value(constraint.text)

            elif constraint.parameter == "class":
                constraint.value = self._extract_class_value(constraint.text)

            elif constraint.parameter == "budget":
                constraint.value = self._extract_budget_value(constraint.text)

            elif constraint.parameter == "stops":
                constraint.value = self._extract_stops_value(constraint.text)

        return constraints

    def _extract_time_value(self, text: str) -> Optional[str]:
        """Extract time value from constraint text"""
        # Match specific times (e.g., "10am", "8:30 pm")
        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', text, re.IGNORECASE)
        if time_match:
            return time_match.group(1)

        # Match time ranges
        time_lower = text.lower()
        if "morning" in time_lower:
            return "morning"
        elif "afternoon" in time_lower:
            return "afternoon"
        elif "evening" in time_lower:
            return "evening"
        elif "night" in time_lower:
            return "night"

        # Match before/after patterns
        before_match = re.search(r'before\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))', text, re.IGNORECASE)
        if before_match:
            return f"before {before_match.group(1)}"

        after_match = re.search(r'after\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))', text, re.IGNORECASE)
        if after_match:
            return f"after {after_match.group(1)}"

        return None

    def _extract_class_value(self, text: str) -> Optional[str]:
        """Extract class value from constraint text"""
        text_lower = text.lower()

        if "business" in text_lower:
            return "business"
        elif "first" in text_lower:
            return "first"
        elif "economy" in text_lower:
            return "economy"
        elif "premium" in text_lower:
            return "premium_economy"

        return None

    def _extract_budget_value(self, text: str) -> Optional[str]:
        """Extract budget value from constraint text"""
        # Match amounts (e.g., "10k", "5000 rupees", "Rs 3000")
        amount_match = re.search(r'(\d+k?)\s*(?:rupees|rs|inr)?', text, re.IGNORECASE)
        if amount_match:
            return amount_match.group(1)

        return None

    def _extract_stops_value(self, text: str) -> Optional[str]:
        """Extract stops preference from constraint text"""
        text_lower = text.lower()

        if "direct" in text_lower or "non-stop" in text_lower or "nonstop" in text_lower:
            return "direct"
        elif "1 stop" in text_lower or "one stop" in text_lower:
            return "1_stop"
        elif "2 stop" in text_lower or "two stop" in text_lower:
            return "2_stops"

        return None

    def _deduplicate_constraints(self, constraints: List[Constraint]) -> List[Constraint]:
        """
        Remove duplicate or overlapping constraints.

        Args:
            constraints: List of detected constraints

        Returns:
            Deduplicated list
        """
        # Group by parameter
        by_param = {}
        for constraint in constraints:
            param = constraint.parameter
            if param not in by_param:
                by_param[param] = []
            by_param[param].append(constraint)

        # For each parameter, keep the strongest constraint
        deduplicated = []
        for param, param_constraints in by_param.items():
            # Sort by strength (descending) then confidence (descending)
            sorted_constraints = sorted(
                param_constraints,
                key=lambda c: (c.strength.value, c.confidence),
                reverse=True
            )
            # Keep the strongest one
            deduplicated.append(sorted_constraints[0])

        return deduplicated

    def get_constraint_summary(self, constraints: List[Constraint]) -> Dict:
        """
        Get summary statistics of detected constraints.

        Args:
            constraints: List of constraints

        Returns:
            Summary dictionary
        """
        summary = {
            "total": len(constraints),
            "by_type": {},
            "by_parameter": {},
            "by_strength": {},
            "mandatory_count": 0,
            "flexible_count": 0
        }

        for constraint in constraints:
            # By type
            type_name = constraint.type.value
            summary["by_type"][type_name] = summary["by_type"].get(type_name, 0) + 1

            # By parameter
            summary["by_parameter"][constraint.parameter] = \
                summary["by_parameter"].get(constraint.parameter, 0) + 1

            # By strength
            strength_name = constraint.strength.name
            summary["by_strength"][strength_name] = \
                summary["by_strength"].get(strength_name, 0) + 1

            # Count mandatory vs flexible
            if constraint.strength == ConstraintStrength.MANDATORY:
                summary["mandatory_count"] += 1
            elif constraint.strength == ConstraintStrength.NONE:
                summary["flexible_count"] += 1

        return summary


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_constraints(constraints: List[Constraint]):
    """Pretty print detected constraints"""
    print("\n" + "="*70)
    print("DETECTED CONSTRAINTS")
    print("="*70)

    if not constraints:
        print("No constraints detected")
        print("="*70)
        return

    # Group by parameter
    by_param = {}
    for constraint in constraints:
        param = constraint.parameter
        if param not in by_param:
            by_param[param] = []
        by_param[param].append(constraint)

    # Print by parameter
    for param, param_constraints in sorted(by_param.items()):
        print(f"\n{param.upper()}:")
        for constraint in param_constraints:
            strength_bar = "#" * int(constraint.strength.value * 10)
            print(f"  [{constraint.type.value:20}] {constraint.text}")
            print(f"    Strength: {constraint.strength.value:.1f} [{strength_bar}] | " +
                  f"Confidence: {constraint.confidence:.2%}")
            if constraint.value:
                print(f"    Value: {constraint.value}")

    print("\n" + "="*70)
