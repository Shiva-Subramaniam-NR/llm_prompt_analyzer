"""
SystemPromptParser - Extracts Structured Requirements from System Prompts

This component parses system prompts to extract:
1. Required parameters (what info the system expects from users)
2. Behavioral constraints (MUST/NEVER directives)
3. Scope definitions (what the system can/cannot do)
4. Output format expectations
5. Safety/ethical guidelines

Uses semantic embeddings to understand requirements without rigid pattern matching.

Author: Prompt Analysis Framework v2
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import re
from v2.embedding_manager import EmbeddingManager


class RequirementType(Enum):
    """Types of requirements that can be extracted"""
    REQUIRED_PARAMETER = "required_parameter"  # User must provide this info
    OPTIONAL_PARAMETER = "optional_parameter"  # User can provide this info
    HARD_CONSTRAINT = "hard_constraint"  # MUST/NEVER rules
    SOFT_CONSTRAINT = "soft_constraint"  # SHOULD/PREFER rules
    SCOPE_DEFINITION = "scope_definition"  # What system can/cannot do
    OUTPUT_FORMAT = "output_format"  # Expected response format
    SAFETY_GUIDELINE = "safety_guideline"  # Ethical/safety rules


class ConstraintPolarity(Enum):
    """Polarity of constraints"""
    POSITIVE = "positive"  # MUST do X, ALWAYS do X
    NEGATIVE = "negative"  # NEVER do X, DON'T do X


@dataclass
class Requirement:
    """Represents a single extracted requirement"""
    type: RequirementType
    content: str  # The actual requirement text
    polarity: Optional[ConstraintPolarity] = None
    confidence: float = 0.0  # 0-1, how confident we are in this extraction
    line_number: int = 0
    keywords: List[str] = field(default_factory=list)  # Key concepts extracted

    def __repr__(self):
        polarity_str = f" ({self.polarity.value})" if self.polarity else ""
        return (
            f"[{self.type.value}{polarity_str}] {self.content}\n"
            f"  Confidence: {self.confidence:.2%} | Line: {self.line_number}"
        )


@dataclass
class ParameterRequirement:
    """Specific parameter that users must/should provide"""
    name: str  # e.g., "origin", "destination", "date"
    description: str  # What this parameter represents
    required: bool  # True = MUST provide, False = OPTIONAL
    examples: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)  # Constraints on this param
    confidence: float = 0.0

    def __repr__(self):
        req_str = "REQUIRED" if self.required else "OPTIONAL"
        return f"[{req_str}] {self.name}: {self.description} (confidence: {self.confidence:.2%})"


@dataclass
class SystemPromptAnalysis:
    """Complete analysis of a system prompt"""
    # Extracted requirements by type
    required_parameters: List[ParameterRequirement]
    optional_parameters: List[ParameterRequirement]
    hard_constraints: List[Requirement]
    soft_constraints: List[Requirement]
    scope_definitions: List[Requirement]
    output_formats: List[Requirement]
    safety_guidelines: List[Requirement]

    # Metadata
    total_requirements: int
    primary_objective: str  # Main purpose of the system
    domain: str  # e.g., "flight_booking", "nutrition", "image_generation"

    def get_all_requirements(self) -> List[Requirement]:
        """Get all requirements as a flat list"""
        all_reqs = []
        all_reqs.extend(self.hard_constraints)
        all_reqs.extend(self.soft_constraints)
        all_reqs.extend(self.scope_definitions)
        all_reqs.extend(self.output_formats)
        all_reqs.extend(self.safety_guidelines)
        return all_reqs

    def get_required_parameter_names(self) -> List[str]:
        """Get list of required parameter names"""
        return [p.name for p in self.required_parameters]

    def has_parameter(self, param_name: str) -> bool:
        """Check if a parameter is mentioned in requirements"""
        all_params = self.required_parameters + self.optional_parameters
        return any(p.name.lower() == param_name.lower() for p in all_params)


class SystemPromptParser:
    """
    Parses system prompts to extract structured requirements.

    Approach:
    1. Segment prompt into sections (role, requirements, constraints, etc.)
    2. Extract parameters using semantic similarity to common parameter types
    3. Classify directives by strength (MUST vs SHOULD)
    4. Identify scope boundaries
    5. Extract output format expectations
    """

    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
        self._initialize_semantic_anchors()

    def _initialize_semantic_anchors(self):
        """Initialize semantic anchors for requirement extraction"""

        # Common parameter types across domains
        self.parameter_anchors = {
            "origin": ["origin location", "departure city", "starting point", "from location", "source location"],
            "destination": ["destination", "arrival city", "target location", "to location", "end point"],
            "date": ["date", "when", "time", "day", "departure date", "travel date"],
            "time": ["time", "hour", "departure time", "arrival time", "specific time"],
            "preference": ["preference", "preferred", "choice", "option", "selection"],
            "budget": ["budget", "price range", "cost limit", "maximum price", "spending limit"],
            "dietary_restriction": ["dietary restriction", "allergies", "food allergies", "cannot eat", "avoid foods"],
            "age": ["age", "how old", "years old", "age group", "child age"],
            "quantity": ["quantity", "how many", "number of", "count", "amount"],
            "category": ["category", "type", "kind", "style", "genre"]
        }

        # Pre-compute parameter anchor embeddings
        self.parameter_embeddings = {}
        for param_name, anchors in self.parameter_anchors.items():
            embeddings = self.embedding_manager.encode_batch(anchors)
            self.parameter_embeddings[param_name] = embeddings

        # Constraint strength indicators
        self.hard_constraint_patterns = [
            r'\b(must|required|mandatory|critical|essential|necessary)\b',
            r'\b(never|always|cannot|can\'t|do not|don\'t)\b',
            r'\b(strictly|absolutely|under no circumstances)\b',
        ]

        self.soft_constraint_patterns = [
            r'\b(should|prefer|recommend|suggest|ideally)\b',
            r'\b(try to|aim to|strive to|attempt to)\b',
        ]

        # Negation words (for polarity detection)
        self.negation_words = {
            "never", "not", "don't", "do not", "cannot", "can't",
            "won't", "will not", "shouldn't", "should not",
            "mustn't", "must not", "no", "avoid", "refrain", "prohibit"
        }

    def parse(self, system_prompt: str) -> SystemPromptAnalysis:
        """
        Parse a system prompt and extract all requirements.

        Args:
            system_prompt: The system prompt text to analyze

        Returns:
            SystemPromptAnalysis with extracted requirements
        """
        # Extract parameters
        required_params, optional_params = self._extract_parameters(system_prompt)

        # Extract constraints
        hard_constraints, soft_constraints = self._extract_constraints(system_prompt)

        # Extract scope definitions
        scope_definitions = self._extract_scope_definitions(system_prompt)

        # Extract output format expectations
        output_formats = self._extract_output_formats(system_prompt)

        # Extract safety guidelines
        safety_guidelines = self._extract_safety_guidelines(system_prompt)

        # Infer primary objective and domain
        primary_objective = self._infer_primary_objective(system_prompt)
        domain = self._infer_domain(system_prompt, required_params)

        total_requirements = (
            len(required_params) + len(optional_params) +
            len(hard_constraints) + len(soft_constraints) +
            len(scope_definitions) + len(output_formats) +
            len(safety_guidelines)
        )

        return SystemPromptAnalysis(
            required_parameters=required_params,
            optional_parameters=optional_params,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            scope_definitions=scope_definitions,
            output_formats=output_formats,
            safety_guidelines=safety_guidelines,
            total_requirements=total_requirements,
            primary_objective=primary_objective,
            domain=domain
        )

    def _extract_parameters(self, prompt: str) -> tuple[List[ParameterRequirement], List[ParameterRequirement]]:
        """
        Extract required and optional parameters from the prompt.

        Uses semantic similarity to identify parameter mentions.
        """
        required_params = []
        optional_params = []

        lines = prompt.split('\n')

        # Look for sections that mention "required" or "information needed"
        in_required_section = False
        in_optional_section = False

        for i, line in enumerate(lines, start=1):
            line_lower = line.lower().strip()

            # Detect section headers
            if re.search(r'\b(required|must provide|needed|necessary)\b', line_lower):
                in_required_section = True
                in_optional_section = False
                continue
            elif re.search(r'\b(optional|may provide|can provide)\b', line_lower):
                in_optional_section = True
                in_required_section = False
                continue
            elif line_lower.startswith('#') or len(line_lower) < 5:
                continue

            # Extract parameters from bullet points or sentences
            if line.strip().startswith('-') or line.strip().startswith('*'):
                param_text = line.strip()[1:].strip()
            else:
                param_text = line.strip()

            if len(param_text) < 5:
                continue

            # Check for parameter matches using semantic similarity
            param_embedding = self.embedding_manager.encode(param_text)

            best_match = None
            best_similarity = 0.0

            for param_name, anchor_embeddings in self.parameter_embeddings.items():
                max_sim = max(
                    self.embedding_manager.cosine_similarity(param_embedding, anchor_emb)
                    for anchor_emb in anchor_embeddings
                )

                if max_sim > best_similarity and max_sim > 0.50:  # Threshold
                    best_similarity = max_sim
                    best_match = param_name

            if best_match:
                param_req = ParameterRequirement(
                    name=best_match,
                    description=param_text,
                    required=in_required_section,
                    confidence=best_similarity
                )

                if in_required_section:
                    required_params.append(param_req)
                else:
                    optional_params.append(param_req)

        return required_params, optional_params

    def _extract_constraints(self, prompt: str) -> tuple[List[Requirement], List[Requirement]]:
        """
        Extract hard and soft constraints from the prompt.

        Hard constraints: MUST, NEVER, ALWAYS
        Soft constraints: SHOULD, PREFER, RECOMMEND
        """
        hard_constraints = []
        soft_constraints = []

        lines = prompt.split('\n')

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            if len(line_stripped) < 10:
                continue

            # Remove bullet points
            if line_stripped.startswith('-') or line_stripped.startswith('*'):
                line_stripped = line_stripped[1:].strip()

            # Check for hard constraints
            is_hard = any(re.search(pattern, line_stripped.lower()) for pattern in self.hard_constraint_patterns)
            is_soft = any(re.search(pattern, line_stripped.lower()) for pattern in self.soft_constraint_patterns)

            if is_hard:
                # Determine polarity
                has_negation = any(neg in line_stripped.lower() for neg in self.negation_words)
                polarity = ConstraintPolarity.NEGATIVE if has_negation else ConstraintPolarity.POSITIVE

                constraint = Requirement(
                    type=RequirementType.HARD_CONSTRAINT,
                    content=line_stripped,
                    polarity=polarity,
                    confidence=0.85,
                    line_number=i
                )
                hard_constraints.append(constraint)

            elif is_soft:
                has_negation = any(neg in line_stripped.lower() for neg in self.negation_words)
                polarity = ConstraintPolarity.NEGATIVE if has_negation else ConstraintPolarity.POSITIVE

                constraint = Requirement(
                    type=RequirementType.SOFT_CONSTRAINT,
                    content=line_stripped,
                    polarity=polarity,
                    confidence=0.75,
                    line_number=i
                )
                soft_constraints.append(constraint)

        return hard_constraints, soft_constraints

    def _extract_scope_definitions(self, prompt: str) -> List[Requirement]:
        """
        Extract scope definitions (what the system can/cannot do).

        Looks for phrases like:
        - "You are a X assistant"
        - "Your role is to..."
        - "You can/cannot..."
        """
        scope_definitions = []

        lines = prompt.split('\n')

        scope_patterns = [
            r'\b(you are|you\'re|your role is|your purpose is)\b',
            r'\b(you can|you cannot|you can\'t|you may|you may not)\b',
            r'\b(your responsibility|you will|you won\'t)\b',
        ]

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            if len(line_stripped) < 10:
                continue

            # Remove bullet points
            if line_stripped.startswith('-') or line_stripped.startswith('*'):
                line_stripped = line_stripped[1:].strip()

            # Check for scope definition patterns
            if any(re.search(pattern, line_stripped.lower()) for pattern in scope_patterns):
                scope_def = Requirement(
                    type=RequirementType.SCOPE_DEFINITION,
                    content=line_stripped,
                    confidence=0.80,
                    line_number=i
                )
                scope_definitions.append(scope_def)

        return scope_definitions

    def _extract_output_formats(self, prompt: str) -> List[Requirement]:
        """
        Extract output format expectations.

        Looks for phrases like:
        - "Respond in JSON format"
        - "Keep responses under X words"
        - "Format as a list"
        """
        output_formats = []

        lines = prompt.split('\n')

        format_patterns = [
            r'\b(format|structure|respond|reply|answer)\b',
            r'\b(json|xml|markdown|list|table)\b',
            r'\b(under \d+ words|within \d+ characters)\b',
        ]

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            if len(line_stripped) < 10:
                continue

            # Remove bullet points
            if line_stripped.startswith('-') or line_stripped.startswith('*'):
                line_stripped = line_stripped[1:].strip()

            # Check for format patterns
            if any(re.search(pattern, line_stripped.lower()) for pattern in format_patterns):
                # Make sure it's about output format, not input
                if not re.search(r'\b(user|input|provide|give me)\b', line_stripped.lower()):
                    output_fmt = Requirement(
                        type=RequirementType.OUTPUT_FORMAT,
                        content=line_stripped,
                        confidence=0.70,
                        line_number=i
                    )
                    output_formats.append(output_fmt)

        return output_formats

    def _extract_safety_guidelines(self, prompt: str) -> List[Requirement]:
        """
        Extract safety and ethical guidelines.

        Looks for phrases related to:
        - Privacy, security
        - Harmful content
        - Ethical boundaries
        """
        safety_guidelines = []

        lines = prompt.split('\n')

        safety_patterns = [
            r'\b(safety|safe|unsafe|harm|harmful)\b',
            r'\b(privacy|private|confidential|personal)\b',
            r'\b(security|secure|protect|sensitive)\b',
            r'\b(ethical|ethics|appropriate|inappropriate)\b',
            r'\b(medical advice|legal advice|financial advice)\b',
        ]

        for i, line in enumerate(lines, start=1):
            line_stripped = line.strip()

            if len(line_stripped) < 10:
                continue

            # Remove bullet points
            if line_stripped.startswith('-') or line_stripped.startswith('*'):
                line_stripped = line_stripped[1:].strip()

            # Check for safety patterns
            if any(re.search(pattern, line_stripped.lower()) for pattern in safety_patterns):
                safety_guideline = Requirement(
                    type=RequirementType.SAFETY_GUIDELINE,
                    content=line_stripped,
                    confidence=0.75,
                    line_number=i
                )
                safety_guidelines.append(safety_guideline)

        return safety_guidelines

    def _infer_primary_objective(self, prompt: str) -> str:
        """
        Infer the primary objective of the system from the prompt.

        Looks at role definitions and purpose statements.
        """
        lines = prompt.split('\n')

        # Look for role definition (usually in first few lines)
        for line in lines[:10]:
            line_lower = line.lower().strip()

            # Match patterns like "You are a X assistant"
            match = re.search(r'you are (?:a |an )?(.*?)(?:assistant|bot|agent|system)', line_lower)
            if match:
                return match.group(1).strip()

            # Match "Your role is to..."
            match = re.search(r'your (?:role|purpose) is to (.*)', line_lower)
            if match:
                return match.group(1).strip()

        return "general assistant"

    def _infer_domain(self, prompt: str, required_params: List[ParameterRequirement]) -> str:
        """
        Infer the domain based on required parameters and keywords.
        """
        # Domain-specific keywords
        domain_keywords = {
            "flight_booking": ["flight", "airline", "airport", "booking", "travel", "departure", "arrival"],
            "nutrition": ["nutrition", "recipe", "food", "meal", "dietary", "calorie", "ingredient"],
            "image_generation": ["image", "picture", "visual", "generate", "create", "style", "design"],
            "customer_support": ["support", "customer", "help", "issue", "ticket", "resolve"],
            "code_review": ["code", "review", "programming", "bug", "function", "refactor"],
        }

        prompt_lower = prompt.lower()

        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            domain_scores[domain] = score

        # Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            if best_domain[1] > 0:
                return best_domain[0]

        return "general"


def print_system_prompt_analysis(analysis: SystemPromptAnalysis):
    """Pretty print system prompt analysis"""
    print("\n" + "="*70)
    print("SYSTEM PROMPT ANALYSIS")
    print("="*70)

    print(f"\nDomain: {analysis.domain}")
    print(f"Primary Objective: {analysis.primary_objective}")
    print(f"Total Requirements Extracted: {analysis.total_requirements}")

    # Required Parameters
    if analysis.required_parameters:
        print(f"\n{'='*70}")
        print(f"REQUIRED PARAMETERS ({len(analysis.required_parameters)})")
        print(f"{'='*70}")
        for param in analysis.required_parameters:
            print(f"\n  {param}")

    # Optional Parameters
    if analysis.optional_parameters:
        print(f"\n{'='*70}")
        print(f"OPTIONAL PARAMETERS ({len(analysis.optional_parameters)})")
        print(f"{'='*70}")
        for param in analysis.optional_parameters:
            print(f"\n  {param}")

    # Hard Constraints
    if analysis.hard_constraints:
        print(f"\n{'='*70}")
        print(f"HARD CONSTRAINTS ({len(analysis.hard_constraints)})")
        print(f"{'='*70}")
        for constraint in analysis.hard_constraints:
            print(f"\n  {constraint}")

    # Soft Constraints
    if analysis.soft_constraints:
        print(f"\n{'='*70}")
        print(f"SOFT CONSTRAINTS ({len(analysis.soft_constraints)})")
        print(f"{'='*70}")
        for constraint in analysis.soft_constraints:
            print(f"\n  {constraint}")

    # Scope Definitions
    if analysis.scope_definitions:
        print(f"\n{'='*70}")
        print(f"SCOPE DEFINITIONS ({len(analysis.scope_definitions)})")
        print(f"{'='*70}")
        for scope in analysis.scope_definitions:
            print(f"\n  {scope}")

    # Output Formats
    if analysis.output_formats:
        print(f"\n{'='*70}")
        print(f"OUTPUT FORMAT EXPECTATIONS ({len(analysis.output_formats)})")
        print(f"{'='*70}")
        for fmt in analysis.output_formats:
            print(f"\n  {fmt}")

    # Safety Guidelines
    if analysis.safety_guidelines:
        print(f"\n{'='*70}")
        print(f"SAFETY GUIDELINES ({len(analysis.safety_guidelines)})")
        print(f"{'='*70}")
        for guideline in analysis.safety_guidelines:
            print(f"\n  {guideline}")

    print("\n" + "="*70)
