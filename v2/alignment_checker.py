"""
AlignmentChecker - Detects Misalignment Between System and User Prompts

This component compares system prompt requirements against user prompts to identify:
1. Missing required parameters
2. Violation of hard constraints
3. Ignored soft constraints
4. Out-of-scope requests
5. Conflicting objectives

Uses semantic similarity to understand user intent even with variations.

Author: Prompt Analysis Framework v2
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import re
from v2.embedding_manager import EmbeddingManager
from v2.system_prompt_parser import SystemPromptParser, SystemPromptAnalysis, RequirementType, ConstraintPolarity


class MisalignmentType(Enum):
    """Types of misalignments between system and user prompts"""
    MISSING_REQUIRED_PARAMETER = "missing_required_parameter"
    CONSTRAINT_VIOLATION = "constraint_violation"
    OUT_OF_SCOPE = "out_of_scope"
    CONFLICTING_OBJECTIVE = "conflicting_objective"
    UNSAFE_REQUEST = "unsafe_request"
    FORMAT_MISMATCH = "format_mismatch"


class MisalignmentSeverity(Enum):
    """Severity levels for misalignments"""
    CRITICAL = 4  # System cannot fulfill request (missing required params)
    HIGH = 3      # Violates hard constraints or safety guidelines
    MODERATE = 2  # Ignores soft constraints or preferences
    LOW = 1       # Minor inconsistencies


@dataclass
class Misalignment:
    """Represents a detected misalignment"""
    type: MisalignmentType
    severity: MisalignmentSeverity
    description: str
    recommendation: str  # How to fix it
    system_requirement: str  # What system expects
    user_content: str  # What user provided (or didn't provide)
    confidence: float = 0.0

    def __repr__(self):
        return (
            f"[{self.severity.name}] {self.type.value}\n"
            f"  Issue: {self.description}\n"
            f"  System expects: {self.system_requirement}\n"
            f"  User provided: {self.user_content}\n"
            f"  Fix: {self.recommendation}\n"
            f"  Confidence: {self.confidence:.2%}"
        )


@dataclass
class AlignmentScore:
    """Overall alignment score between system and user prompts"""
    overall_score: float  # 0-10, higher = better alignment
    completeness: float   # 0-10, all required params provided?
    constraint_adherence: float  # 0-10, follows constraints?
    scope_match: float    # 0-10, request within scope?
    safety_compliance: float  # 0-10, respects safety guidelines?

    def is_aligned(self, threshold: float = 7.0) -> bool:
        """Check if prompts are sufficiently aligned"""
        return self.overall_score >= threshold

    def __repr__(self):
        return (
            f"Alignment Score: {self.overall_score:.1f}/10\n"
            f"  Completeness: {self.completeness:.1f}/10\n"
            f"  Constraint Adherence: {self.constraint_adherence:.1f}/10\n"
            f"  Scope Match: {self.scope_match:.1f}/10\n"
            f"  Safety Compliance: {self.safety_compliance:.1f}/10"
        )


@dataclass
class AlignmentAnalysis:
    """Complete alignment analysis between system and user prompts"""
    misalignments: List[Misalignment]
    alignment_score: AlignmentScore

    # Counts by severity
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int

    # User prompt analysis
    detected_parameters: Dict[str, str]  # param_name -> value found
    detected_intent: str  # What user is trying to do

    def is_fulfillable(self) -> bool:
        """Can system fulfill this user request?"""
        return self.critical_count == 0 and self.alignment_score.overall_score >= 5.0

    def has_critical_issues(self) -> bool:
        """Are there critical misalignments?"""
        return self.critical_count > 0 or self.high_count > 0


class AlignmentChecker:
    """
    Checks alignment between system prompt requirements and user prompts.

    Approach:
    1. Parse system prompt to extract requirements (via SystemPromptParser)
    2. Extract parameters and intent from user prompt
    3. Check for missing required parameters
    4. Detect constraint violations
    5. Verify scope compatibility
    6. Calculate alignment scores
    """

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        system_prompt_parser: SystemPromptParser,
        similarity_threshold: float = 0.60
    ):
        self.embedding_manager = embedding_manager
        self.system_prompt_parser = system_prompt_parser
        self.similarity_threshold = similarity_threshold

    def check_alignment(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> AlignmentAnalysis:
        """
        Check alignment between system and user prompts.

        Args:
            system_prompt: The system prompt defining requirements
            user_prompt: The user prompt to check against requirements

        Returns:
            AlignmentAnalysis with detected misalignments and scores
        """
        # Parse system prompt
        system_analysis = self.system_prompt_parser.parse(system_prompt)

        # Extract info from user prompt
        detected_params = self._extract_parameters_from_user(user_prompt, system_analysis)
        detected_intent = self._infer_user_intent(user_prompt)

        # Check for misalignments
        misalignments = []

        # 1. Check for missing required parameters
        missing_param_misalignments = self._check_missing_parameters(
            system_analysis, detected_params
        )
        misalignments.extend(missing_param_misalignments)

        # 2. Check for constraint violations
        constraint_violations = self._check_constraint_violations(
            system_analysis, user_prompt
        )
        misalignments.extend(constraint_violations)

        # 3. Check for out-of-scope requests
        scope_violations = self._check_scope_violations(
            system_analysis, user_prompt, detected_intent
        )
        misalignments.extend(scope_violations)

        # 4. Check safety guideline violations
        safety_violations = self._check_safety_violations(
            system_analysis, user_prompt
        )
        misalignments.extend(safety_violations)

        # Calculate severity counts
        critical_count = sum(1 for m in misalignments if m.severity == MisalignmentSeverity.CRITICAL)
        high_count = sum(1 for m in misalignments if m.severity == MisalignmentSeverity.HIGH)
        moderate_count = sum(1 for m in misalignments if m.severity == MisalignmentSeverity.MODERATE)
        low_count = sum(1 for m in misalignments if m.severity == MisalignmentSeverity.LOW)

        # Calculate alignment scores
        alignment_score = self._calculate_alignment_score(
            system_analysis, detected_params, misalignments
        )

        return AlignmentAnalysis(
            misalignments=misalignments,
            alignment_score=alignment_score,
            critical_count=critical_count,
            high_count=high_count,
            moderate_count=moderate_count,
            low_count=low_count,
            detected_parameters=detected_params,
            detected_intent=detected_intent
        )

    def _extract_parameters_from_user(
        self,
        user_prompt: str,
        system_analysis: SystemPromptAnalysis
    ) -> Dict[str, str]:
        """
        Extract parameters from user prompt based on system expectations.

        Directly tries to extract parameter values using patterns.
        """
        detected_params = {}

        # Get all expected parameters (required + optional)
        all_params = system_analysis.required_parameters + system_analysis.optional_parameters

        for param in all_params:
            # Try to extract the actual value directly
            value = self._extract_parameter_value(user_prompt, param.name)
            if value:
                detected_params[param.name] = value

        return detected_params

    def _extract_parameter_value(self, user_prompt: str, param_name: str) -> Optional[str]:
        """
        Extract the actual value for a parameter from user prompt.

        This is a simplified extraction - production would use NER.
        """
        user_lower = user_prompt.lower()

        # Parameter-specific extraction patterns
        if param_name == "origin":
            # Look for "from X", "leaving from X", "departing X"
            patterns = [
                r'from\s+([A-Za-z\s]+?)(?:\s+to|\s+on|\s*$)',
                r'leaving\s+from\s+([A-Za-z\s]+?)(?:\s+to|\s+on|\s*$)',
                r'depart(?:ing)?\s+([A-Za-z\s]+?)(?:\s+to|\s+on|\s*$)',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    return match.group(1).strip()

        elif param_name == "destination":
            # Look for "to X", "going to X", "arrive at X"
            patterns = [
                r'to\s+([A-Za-z\s]+?)(?:\s+on|\s+tomorrow|\s*$)',
                r'going\s+to\s+([A-Za-z\s]+?)(?:\s+on|\s+tomorrow|\s*$)',
                r'arriv(?:e|ing)\s+(?:at|in)\s+([A-Za-z\s]+?)(?:\s+on|\s*$)',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    return match.group(1).strip()

        elif param_name == "date":
            # Look for dates (tomorrow, next week, specific dates)
            patterns = [
                r'(tomorrow|today|next week|next month)',
                r'on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    return match.group(1).strip()

        elif param_name == "age":
            patterns = [
                r'(\d+)\s*(?:year|yr)s?\s*old',
                r'age\s+(\d+)',
                r'for\s+(?:a\s+)?(\d+)\s*(?:year|yr)',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    return match.group(1).strip()

        elif param_name == "budget":
            patterns = [
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'under\s+\$?(\d+)',
                r'budget\s+(?:of\s+)?\$?(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, user_lower)
                if match:
                    return f"${match.group(1)}"

        # Generic: if parameter name appears in prompt, mark as "mentioned"
        if param_name in user_lower:
            return "mentioned"

        return None

    def _infer_user_intent(self, user_prompt: str) -> str:
        """
        Infer what the user is trying to do.

        Returns a simple intent label like "booking", "inquiry", "modification"
        """
        user_lower = user_prompt.lower()

        # Intent patterns
        if any(word in user_lower for word in ["book", "reserve", "schedule", "plan"]):
            return "booking"
        elif any(word in user_lower for word in ["find", "search", "show", "what", "which"]):
            return "inquiry"
        elif any(word in user_lower for word in ["change", "modify", "update", "cancel"]):
            return "modification"
        elif any(word in user_lower for word in ["help", "how", "can you"]):
            return "help_request"
        else:
            return "general"

    def _check_missing_parameters(
        self,
        system_analysis: SystemPromptAnalysis,
        detected_params: Dict[str, str]
    ) -> List[Misalignment]:
        """Check for missing required parameters"""
        misalignments = []

        for param in system_analysis.required_parameters:
            if param.name not in detected_params:
                misalignment = Misalignment(
                    type=MisalignmentType.MISSING_REQUIRED_PARAMETER,
                    severity=MisalignmentSeverity.CRITICAL,
                    description=f"Missing required parameter: {param.name}",
                    system_requirement=param.description,
                    user_content="Not provided",
                    recommendation=f"Add {param.name} to the user prompt. Example: {param.description}",
                    confidence=0.95
                )
                misalignments.append(misalignment)

        return misalignments

    def _check_constraint_violations(
        self,
        system_analysis: SystemPromptAnalysis,
        user_prompt: str
    ) -> List[Misalignment]:
        """Check if user prompt violates hard or soft constraints"""
        misalignments = []

        user_embedding = self.embedding_manager.encode(user_prompt)

        # Check hard constraints
        for constraint in system_analysis.hard_constraints:
            # Embed constraint
            constraint_embedding = self.embedding_manager.encode(constraint.content)
            similarity = self.embedding_manager.cosine_similarity(user_embedding, constraint_embedding)

            # For NEGATIVE constraints (NEVER/DON'T), high similarity = violation
            if constraint.polarity == ConstraintPolarity.NEGATIVE and similarity > 0.65:
                misalignment = Misalignment(
                    type=MisalignmentType.CONSTRAINT_VIOLATION,
                    severity=MisalignmentSeverity.HIGH,
                    description=f"User request violates hard constraint",
                    system_requirement=constraint.content,
                    user_content=user_prompt,
                    recommendation="Modify user prompt to comply with system constraint",
                    confidence=similarity
                )
                misalignments.append(misalignment)

            # For POSITIVE constraints (MUST/ALWAYS), check if requirement is met
            # This is complex - simplified for now
            elif constraint.polarity == ConstraintPolarity.POSITIVE and similarity < 0.30:
                # User prompt doesn't align with what system must do
                # This is a warning, not critical
                pass  # Skip for now to avoid false positives

        # Check soft constraints (lower severity)
        for constraint in system_analysis.soft_constraints:
            constraint_embedding = self.embedding_manager.encode(constraint.content)
            similarity = self.embedding_manager.cosine_similarity(user_embedding, constraint_embedding)

            # For NEGATIVE soft constraints (SHOULD NOT), similarity = minor violation
            if constraint.polarity == ConstraintPolarity.NEGATIVE and similarity > 0.70:
                misalignment = Misalignment(
                    type=MisalignmentType.CONSTRAINT_VIOLATION,
                    severity=MisalignmentSeverity.MODERATE,
                    description=f"User request conflicts with soft constraint",
                    system_requirement=constraint.content,
                    user_content=user_prompt,
                    recommendation="Consider revising to align with system preferences",
                    confidence=similarity
                )
                misalignments.append(misalignment)

        return misalignments

    def _check_scope_violations(
        self,
        system_analysis: SystemPromptAnalysis,
        user_prompt: str,
        user_intent: str
    ) -> List[Misalignment]:
        """Check if user request is within system scope"""
        misalignments = []

        # Check against scope definitions
        for scope_def in system_analysis.scope_definitions:
            scope_lower = scope_def.content.lower()

            # Look for "cannot" or "can't" in scope definition
            if "cannot" in scope_lower or "can't" in scope_lower:
                # Extract what system cannot do
                # e.g., "You cannot provide medical advice"

                # Check if user is asking for prohibited functionality
                user_embedding = self.embedding_manager.encode(user_prompt)
                scope_embedding = self.embedding_manager.encode(scope_def.content)
                similarity = self.embedding_manager.cosine_similarity(user_embedding, scope_embedding)

                if similarity > 0.60:
                    misalignment = Misalignment(
                        type=MisalignmentType.OUT_OF_SCOPE,
                        severity=MisalignmentSeverity.HIGH,
                        description="User request is outside system capabilities",
                        system_requirement=scope_def.content,
                        user_content=user_prompt,
                        recommendation="User should request functionality within system scope",
                        confidence=similarity
                    )
                    misalignments.append(misalignment)

        # Check if user intent matches system objective
        if system_analysis.primary_objective:
            objective_lower = system_analysis.primary_objective.lower()

            # Simple mismatch detection
            intent_objective_mismatch = False

            if "booking" in objective_lower and user_intent not in ["booking", "inquiry", "help_request"]:
                intent_objective_mismatch = True
            elif "nutrition" in objective_lower and user_intent not in ["inquiry", "help_request"]:
                intent_objective_mismatch = True

            if intent_objective_mismatch:
                misalignment = Misalignment(
                    type=MisalignmentType.CONFLICTING_OBJECTIVE,
                    severity=MisalignmentSeverity.MODERATE,
                    description=f"User intent '{user_intent}' may not match system objective '{system_analysis.primary_objective}'",
                    system_requirement=f"System is designed for {system_analysis.primary_objective}",
                    user_content=f"User intent: {user_intent}",
                    recommendation="Verify user intent aligns with system purpose",
                    confidence=0.70
                )
                misalignments.append(misalignment)

        return misalignments

    def _check_safety_violations(
        self,
        system_analysis: SystemPromptAnalysis,
        user_prompt: str
    ) -> List[Misalignment]:
        """Check if user prompt violates safety guidelines"""
        misalignments = []

        user_embedding = self.embedding_manager.encode(user_prompt)

        for guideline in system_analysis.safety_guidelines:
            guideline_embedding = self.embedding_manager.encode(guideline.content)
            similarity = self.embedding_manager.cosine_similarity(user_embedding, guideline_embedding)

            # If user prompt is similar to a safety guideline mentioning prohibited content
            # This might indicate a violation
            guideline_lower = guideline.content.lower()

            if any(word in guideline_lower for word in ["cannot", "never", "avoid", "don't"]):
                if similarity > 0.65:
                    misalignment = Misalignment(
                        type=MisalignmentType.UNSAFE_REQUEST,
                        severity=MisalignmentSeverity.HIGH,
                        description="User request may violate safety guidelines",
                        system_requirement=guideline.content,
                        user_content=user_prompt,
                        recommendation="Modify request to comply with safety guidelines",
                        confidence=similarity
                    )
                    misalignments.append(misalignment)

        return misalignments

    def _calculate_alignment_score(
        self,
        system_analysis: SystemPromptAnalysis,
        detected_params: Dict[str, str],
        misalignments: List[Misalignment]
    ) -> AlignmentScore:
        """Calculate overall alignment score"""

        # 1. Completeness (required parameters provided)
        required_param_count = len(system_analysis.required_parameters)
        if required_param_count > 0:
            provided_required = sum(
                1 for param in system_analysis.required_parameters
                if param.name in detected_params
            )
            completeness = (provided_required / required_param_count) * 10.0
        else:
            completeness = 10.0

        # 2. Constraint Adherence
        constraint_violations = [
            m for m in misalignments
            if m.type == MisalignmentType.CONSTRAINT_VIOLATION
        ]

        total_constraints = len(system_analysis.hard_constraints) + len(system_analysis.soft_constraints)
        if total_constraints > 0:
            violation_penalty = len(constraint_violations) * 2.0
            constraint_adherence = max(0.0, 10.0 - violation_penalty)
        else:
            constraint_adherence = 10.0

        # 3. Scope Match
        scope_violations = [
            m for m in misalignments
            if m.type in [MisalignmentType.OUT_OF_SCOPE, MisalignmentType.CONFLICTING_OBJECTIVE]
        ]
        scope_match = max(0.0, 10.0 - (len(scope_violations) * 3.0))

        # 4. Safety Compliance
        safety_violations = [
            m for m in misalignments
            if m.type == MisalignmentType.UNSAFE_REQUEST
        ]
        safety_compliance = max(0.0, 10.0 - (len(safety_violations) * 4.0))

        # Overall score (weighted average)
        overall_score = (
            0.35 * completeness +
            0.25 * constraint_adherence +
            0.20 * scope_match +
            0.20 * safety_compliance
        )

        return AlignmentScore(
            overall_score=overall_score,
            completeness=completeness,
            constraint_adherence=constraint_adherence,
            scope_match=scope_match,
            safety_compliance=safety_compliance
        )


def print_alignment_analysis(analysis: AlignmentAnalysis):
    """Pretty print alignment analysis"""
    print("\n" + "="*70)
    print("ALIGNMENT ANALYSIS - SYSTEM vs USER PROMPT")
    print("="*70)

    print(f"\n{analysis.alignment_score}")

    print(f"\nMisalignments Found: {len(analysis.misalignments)}")
    print(f"  - CRITICAL: {analysis.critical_count}")
    print(f"  - HIGH: {analysis.high_count}")
    print(f"  - MODERATE: {analysis.moderate_count}")
    print(f"  - LOW: {analysis.low_count}")

    print(f"\nUser Intent: {analysis.detected_intent}")
    print(f"Parameters Detected: {len(analysis.detected_parameters)}")
    for param_name, value in analysis.detected_parameters.items():
        print(f"  - {param_name}: {value}")

    if analysis.is_fulfillable():
        print(f"\n[OK] System can fulfill this user request")
    else:
        print(f"\n[BLOCKED] System CANNOT fulfill request due to critical issues")

    if analysis.misalignments:
        print(f"\n{'='*70}")
        print("DETECTED MISALIGNMENTS")
        print(f"{'='*70}")

        # Sort by severity
        sorted_misalignments = sorted(
            analysis.misalignments,
            key=lambda m: m.severity.value,
            reverse=True
        )

        for i, misalignment in enumerate(sorted_misalignments, 1):
            print(f"\n{i}. {misalignment}")
    else:
        print(f"\n[PERFECT ALIGNMENT] No misalignments detected!")

    print("\n" + "="*70)
