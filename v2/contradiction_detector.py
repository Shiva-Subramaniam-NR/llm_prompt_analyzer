"""
ContradictionDetector - Identifies Internal Conflicts Within Single Prompts

Uses semantic embeddings to detect contradictions between different statements
in a prompt. Instead of relying on keyword patterns, this uses:

1. Semantic similarity between directive pairs
2. Negation detection
3. Constraint conflict analysis
4. Behavioral incompatibility detection

Author: Prompt Analysis Framework v2
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
import numpy as np
import re
from v2.embedding_manager import EmbeddingManager


class ContradictionType(Enum):
    """Types of contradictions detected"""
    DIRECT_NEGATION = "direct_negation"  # "Do X" vs "Don't do X"
    BEHAVIORAL_CONFLICT = "behavioral_conflict"  # "Be formal" vs "Use casual language"
    CONSTRAINT_MISMATCH = "constraint_mismatch"  # "Keep brief" vs "Provide detailed explanations"
    PERMISSION_CONFLICT = "permission_conflict"  # "Never refuse" vs "Politely decline inappropriate requests"
    SCOPE_CONFLICT = "scope_conflict"  # "Always verify" vs "Skip verification for trusted sources"


class ContradictionSeverity(Enum):
    """Severity levels for contradictions"""
    CRITICAL = 4  # Complete logical contradiction (e.g., "Always X" vs "Never X")
    HIGH = 3  # Strong conflict in behavior (e.g., "Be concise" vs "Explain everything in detail")
    MODERATE = 2  # Partial conflict requiring prioritization (e.g., "Prefer X" vs "Prefer Y")
    LOW = 1  # Minor tension, may be resolvable (e.g., "Be friendly" vs "Maintain professionalism")


@dataclass
class Contradiction:
    """Represents a detected contradiction"""
    type: ContradictionType
    severity: ContradictionSeverity
    statement1: str
    statement2: str
    explanation: str
    confidence: float  # 0-1
    line1: int  # Line number of first statement
    line2: int  # Line number of second statement

    def __repr__(self):
        severity_label = self.severity.name
        return (
            f"[{severity_label}] {self.type.value}\n"
            f"  Statement 1 (line {self.line1}): \"{self.statement1}\"\n"
            f"  Statement 2 (line {self.line2}): \"{self.statement2}\"\n"
            f"  Explanation: {self.explanation}\n"
            f"  Confidence: {self.confidence:.2%}"
        )


@dataclass
class ContradictionAnalysis:
    """Complete contradiction analysis results"""
    contradictions: List[Contradiction]
    total_directives: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    overall_consistency_score: float  # 0-10, higher = more consistent

    def has_critical_contradictions(self) -> bool:
        return self.critical_count > 0

    def has_any_contradictions(self) -> bool:
        return len(self.contradictions) > 0


class ContradictionDetector:
    """
    Detects contradictions within a single prompt using semantic analysis.

    Approach:
    1. Segment prompt into individual directives
    2. Detect negation patterns
    3. Compare directive pairs for semantic conflicts
    4. Classify contradiction type and severity
    """

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        conflict_threshold: float = 0.65,  # Lower threshold for better detection
        negation_threshold: float = 0.65
    ):
        self.embedding_manager = embedding_manager
        self.conflict_threshold = conflict_threshold
        self.negation_threshold = negation_threshold

        # Define contradiction patterns
        self._initialize_contradiction_anchors()

    def _initialize_contradiction_anchors(self):
        """Initialize semantic anchors for contradiction detection"""

        # Behavioral opposites
        self.behavioral_opposites = {
            "formality": {
                "formal": ["be formal", "maintain professional tone", "use formal language", "conservative style"],
                "casual": ["be casual", "use informal language", "relaxed tone", "friendly and approachable"]
            },
            "brevity": {
                "concise": ["be brief", "keep it short", "concise responses", "minimal explanation"],
                "detailed": ["be detailed", "provide thorough explanations", "comprehensive answers", "elaborate on details"]
            },
            "flexibility": {
                "strict": ["always follow rules", "never deviate", "strict adherence", "mandatory compliance"],
                "flexible": ["be flexible", "adapt as needed", "use judgment", "exceptions allowed"]
            },
            "permission": {
                "permissive": ["never refuse", "always help", "accommodate all requests", "fulfill any request"],
                "restrictive": ["decline inappropriate requests", "refuse when necessary", "reject unsuitable queries"]
            },
            "verification": {
                "verify": ["always verify", "double-check everything", "confirm accuracy", "validate sources"],
                "skip": ["skip verification", "assume correctness", "trust without checking", "no need to verify"]
            }
        }

        # Pre-compute embeddings for behavioral anchors
        self.behavioral_embeddings = {}
        for category, opposites in self.behavioral_opposites.items():
            self.behavioral_embeddings[category] = {}
            for polarity, phrases in opposites.items():
                embeddings = self.embedding_manager.encode_batch(phrases)
                self.behavioral_embeddings[category][polarity] = embeddings

        # Negation patterns
        self.negation_words = {
            "never", "not", "don't", "do not", "cannot", "can't",
            "won't", "will not", "shouldn't", "should not",
            "mustn't", "must not", "no", "none", "neither", "nor",
            "avoid", "refrain", "prohibit", "forbidden"
        }

        # Absolute modifiers (increase contradiction severity)
        self.absolute_modifiers = {
            "always", "never", "all", "every", "must", "mandatory",
            "required", "critical", "essential", "absolutely", "definitely",
            "certainly", "under no circumstances", "at all times"
        }

    def detect(self, prompt: str) -> ContradictionAnalysis:
        """
        Detect all contradictions within the prompt.

        Args:
            prompt: The prompt text to analyze

        Returns:
            ContradictionAnalysis with detected contradictions
        """
        # Segment prompt into directives
        directives = self._segment_into_directives(prompt)

        if len(directives) < 2:
            return ContradictionAnalysis(
                contradictions=[],
                total_directives=len(directives),
                critical_count=0,
                high_count=0,
                moderate_count=0,
                low_count=0,
                overall_consistency_score=10.0
            )

        # Detect contradictions between directive pairs
        contradictions = []

        for i in range(len(directives)):
            for j in range(i + 1, len(directives)):
                dir1, line1 = directives[i]
                dir2, line2 = directives[j]

                # Check for direct negation
                negation_conflict = self._check_negation_conflict(dir1, dir2)
                if negation_conflict:
                    contradictions.append(
                        Contradiction(
                            type=ContradictionType.DIRECT_NEGATION,
                            severity=negation_conflict['severity'],
                            statement1=dir1,
                            statement2=dir2,
                            explanation=negation_conflict['explanation'],
                            confidence=negation_conflict['confidence'],
                            line1=line1,
                            line2=line2
                        )
                    )

                # Check for behavioral conflicts
                behavioral_conflict = self._check_behavioral_conflict(dir1, dir2)
                if behavioral_conflict:
                    contradictions.append(
                        Contradiction(
                            type=ContradictionType.BEHAVIORAL_CONFLICT,
                            severity=behavioral_conflict['severity'],
                            statement1=dir1,
                            statement2=dir2,
                            explanation=behavioral_conflict['explanation'],
                            confidence=behavioral_conflict['confidence'],
                            line1=line1,
                            line2=line2
                        )
                    )

                # Check for constraint mismatches
                constraint_conflict = self._check_constraint_conflict(dir1, dir2)
                if constraint_conflict:
                    contradictions.append(
                        Contradiction(
                            type=ContradictionType.CONSTRAINT_MISMATCH,
                            severity=constraint_conflict['severity'],
                            statement1=dir1,
                            statement2=dir2,
                            explanation=constraint_conflict['explanation'],
                            confidence=constraint_conflict['confidence'],
                            line1=line1,
                            line2=line2
                        )
                    )

        # Calculate severity counts
        critical_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.CRITICAL)
        high_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.HIGH)
        moderate_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.MODERATE)
        low_count = sum(1 for c in contradictions if c.severity == ContradictionSeverity.LOW)

        # Calculate consistency score (0-10, higher = more consistent)
        consistency_score = self._calculate_consistency_score(
            total_directives=len(directives),
            contradictions=contradictions
        )

        return ContradictionAnalysis(
            contradictions=contradictions,
            total_directives=len(directives),
            critical_count=critical_count,
            high_count=high_count,
            moderate_count=moderate_count,
            low_count=low_count,
            overall_consistency_score=consistency_score
        )

    def _segment_into_directives(self, prompt: str) -> List[Tuple[str, int]]:
        """
        Segment prompt into individual directive statements.

        Returns:
            List of (directive_text, line_number) tuples
        """
        directives = []

        # Split by common delimiters
        lines = prompt.split('\n')

        for i, line in enumerate(lines, start=1):
            original_line = line
            line = line.strip()

            # Skip empty lines
            if not line or len(line) < 10:
                continue

            # Skip section headers (but NOT bullet points)
            if line.startswith('#') or line.startswith('='):
                continue
            if line == '-' * len(line):  # Skip separator lines like "---"
                continue

            # Remove bullet points but keep the content
            if line.startswith('-') or line.startswith('*'):
                line = line[1:].strip()

            # Remove numbered list prefixes (1., 2., etc.)
            line = re.sub(r'^\d+\.\s*', '', line)

            # Skip if too short after cleaning
            if len(line) < 10:
                continue

            # Split by sentence boundaries (. ! ;)
            sentences = re.split(r'[.!;]\s+', line)

            for sentence in sentences:
                sentence = sentence.strip()

                # Only include directive-like statements
                if self._is_directive(sentence):
                    directives.append((sentence, i))

        return directives

    def _is_directive(self, text: str) -> bool:
        """Check if text is a directive statement"""
        if len(text) < 10:
            return False

        # Directive indicators
        directive_patterns = [
            r'\b(must|should|need to|have to|required to)\b',
            r'\b(never|always|don\'t|do not|cannot)\b',
            r'\b(ensure|make sure|remember to|be sure to)\b',
            r'\b(avoid|refrain|prevent|prohibit)\b',
            r'\b(prefer|ideally|recommend|suggest)\b',
            r'^(be |provide |maintain |use |keep |give |include |skip |decline |refuse |verify |admit |express )',
        ]

        text_lower = text.lower()
        for pattern in directive_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _check_negation_conflict(self, dir1: str, dir2: str) -> Optional[dict]:
        """
        Check if two directives are direct negations of each other.

        Example: "Always verify sources" vs "Never verify sources"
        """
        dir1_lower = dir1.lower()
        dir2_lower = dir2.lower()

        # Check if one is negated and other is positive
        dir1_negated = any(neg in dir1_lower for neg in self.negation_words)
        dir2_negated = any(neg in dir2_lower for neg in self.negation_words)

        # If both are negated or both are positive, no direct negation
        if dir1_negated == dir2_negated:
            return None

        # Remove negation words and compare semantic similarity
        dir1_positive = self._remove_negation(dir1_lower)
        dir2_positive = self._remove_negation(dir2_lower)

        # Embed both
        emb1 = self.embedding_manager.encode(dir1_positive)
        emb2 = self.embedding_manager.encode(dir2_positive)

        similarity = self.embedding_manager.cosine_similarity(emb1, emb2)

        # High similarity after removing negation = direct contradiction
        if similarity >= self.negation_threshold:
            # Check for absolute modifiers
            has_absolute = any(
                mod in dir1_lower or mod in dir2_lower
                for mod in self.absolute_modifiers
            )

            severity = ContradictionSeverity.CRITICAL if has_absolute else ContradictionSeverity.HIGH

            return {
                'severity': severity,
                'explanation': f"Direct negation: one directive prohibits what the other requires (similarity: {similarity:.2%})",
                'confidence': similarity
            }

        return None

    def _check_behavioral_conflict(self, dir1: str, dir2: str) -> Optional[dict]:
        """
        Check if two directives represent conflicting behavioral expectations.

        Example: "Be formal and professional" vs "Use casual, friendly language"
        """
        emb1 = self.embedding_manager.encode(dir1)
        emb2 = self.embedding_manager.encode(dir2)

        # Check against behavioral opposites
        for category, opposites in self.behavioral_embeddings.items():
            polarities = list(opposites.keys())

            # Get max similarity to each polarity
            sim1_to_pol1 = max(
                self.embedding_manager.cosine_similarity(emb1, anchor)
                for anchor in opposites[polarities[0]]
            )
            sim1_to_pol2 = max(
                self.embedding_manager.cosine_similarity(emb1, anchor)
                for anchor in opposites[polarities[1]]
            )

            sim2_to_pol1 = max(
                self.embedding_manager.cosine_similarity(emb2, anchor)
                for anchor in opposites[polarities[0]]
            )
            sim2_to_pol2 = max(
                self.embedding_manager.cosine_similarity(emb2, anchor)
                for anchor in opposites[polarities[1]]
            )

            # Check if dir1 aligns with pol1 and dir2 aligns with pol2 (or vice versa)
            if (sim1_to_pol1 > self.conflict_threshold and sim2_to_pol2 > self.conflict_threshold):
                avg_confidence = (sim1_to_pol1 + sim2_to_pol2) / 2

                # Determine severity based on confidence and category
                # Formality and permission conflicts are typically HIGH severity
                if category in ['formality', 'permission'] and avg_confidence >= 0.70:
                    severity = ContradictionSeverity.HIGH
                elif avg_confidence >= 0.80:
                    severity = ContradictionSeverity.HIGH
                elif avg_confidence >= 0.70:
                    severity = ContradictionSeverity.MODERATE
                else:
                    severity = ContradictionSeverity.LOW

                return {
                    'severity': severity,
                    'explanation': f"Conflicting behavioral expectations in '{category}' (dir1 -> {polarities[0]}, dir2 -> {polarities[1]})",
                    'confidence': avg_confidence
                }

            if (sim1_to_pol2 > self.conflict_threshold and sim2_to_pol1 > self.conflict_threshold):
                avg_confidence = (sim1_to_pol2 + sim2_to_pol1) / 2

                # Determine severity based on confidence and category
                if category in ['formality', 'permission'] and avg_confidence >= 0.70:
                    severity = ContradictionSeverity.HIGH
                elif avg_confidence >= 0.80:
                    severity = ContradictionSeverity.HIGH
                elif avg_confidence >= 0.70:
                    severity = ContradictionSeverity.MODERATE
                else:
                    severity = ContradictionSeverity.LOW

                return {
                    'severity': severity,
                    'explanation': f"Conflicting behavioral expectations in '{category}' (dir1 -> {polarities[1]}, dir2 -> {polarities[0]})",
                    'confidence': avg_confidence
                }

        return None

    def _check_constraint_conflict(self, dir1: str, dir2: str) -> Optional[dict]:
        """
        Check if two directives impose incompatible constraints.

        Example: "Keep responses under 50 words" vs "Provide detailed, comprehensive explanations"
        """
        # Define constraint conflict anchors
        constraint_conflicts = [
            {
                "type": "length",
                "constraint1": ["keep brief", "be concise", "short responses", "under 50 words", "minimal explanation", "keep responses brief"],
                "constraint2": ["provide detailed explanations", "thorough answers", "comprehensive coverage", "elaborate in detail", "include step-by-step instructions", "detailed comprehensive explanations"]
            },
            {
                "type": "scope",
                "constraint1": ["never refuse", "always help", "accommodate all requests", "never refuse any requests", "always provide recipes"],
                "constraint2": ["decline inappropriate requests", "refuse when necessary", "politely reject", "politely decline requests", "decline recipe requests"]
            },
            {
                "type": "certainty",
                "constraint1": ["always be certain", "never express doubt", "confident answers only", "absolutely certain in responses", "never express uncertainty"],
                "constraint2": ["admit uncertainty", "say when unsure", "express limitations", "admit when unsure", "express your limitations"]
            },
            {
                "type": "verification",
                "constraint1": ["always verify", "double-check everything", "verify information from multiple sources", "always double-check all data sources"],
                "constraint2": ["skip verification", "assume correctness", "trust without checking", "no need to verify", "skip verification for trusted sources"]
            },
            {
                "type": "flexibility",
                "constraint1": ["be flexible", "use judgment", "adapt to context", "extremely flexible in interpreting"],
                "constraint2": ["apply rules strictly", "follow rules consistently", "strict adherence", "apply all rules strictly without exceptions"]
            }
        ]

        emb1 = self.embedding_manager.encode(dir1)
        emb2 = self.embedding_manager.encode(dir2)

        for conflict in constraint_conflicts:
            # Encode constraint anchors
            c1_embeddings = self.embedding_manager.encode_batch(conflict["constraint1"])
            c2_embeddings = self.embedding_manager.encode_batch(conflict["constraint2"])

            # Check if dir1 matches constraint1 and dir2 matches constraint2
            sim1_to_c1 = max(
                self.embedding_manager.cosine_similarity(emb1, c1_emb)
                for c1_emb in c1_embeddings
            )
            sim2_to_c2 = max(
                self.embedding_manager.cosine_similarity(emb2, c2_emb)
                for c2_emb in c2_embeddings
            )

            if sim1_to_c1 > self.conflict_threshold and sim2_to_c2 > self.conflict_threshold:
                avg_confidence = (sim1_to_c1 + sim2_to_c2) / 2

                # Constraint conflicts are typically HIGH severity
                severity = (
                    ContradictionSeverity.HIGH if avg_confidence >= 0.70
                    else ContradictionSeverity.MODERATE
                )

                return {
                    'severity': severity,
                    'explanation': f"Incompatible constraints on '{conflict['type']}' - directives cannot both be satisfied",
                    'confidence': avg_confidence
                }

            # Check reverse (dir1 matches constraint2, dir2 matches constraint1)
            sim1_to_c2 = max(
                self.embedding_manager.cosine_similarity(emb1, c2_emb)
                for c2_emb in c2_embeddings
            )
            sim2_to_c1 = max(
                self.embedding_manager.cosine_similarity(emb2, c1_emb)
                for c1_emb in c1_embeddings
            )

            if sim1_to_c2 > self.conflict_threshold and sim2_to_c1 > self.conflict_threshold:
                avg_confidence = (sim1_to_c2 + sim2_to_c1) / 2

                # Constraint conflicts are typically HIGH severity
                severity = (
                    ContradictionSeverity.HIGH if avg_confidence >= 0.70
                    else ContradictionSeverity.MODERATE
                )

                return {
                    'severity': severity,
                    'explanation': f"Incompatible constraints on '{conflict['type']}' - directives cannot both be satisfied",
                    'confidence': avg_confidence
                }

        return None

    def _remove_negation(self, text: str) -> str:
        """Remove negation words from text"""
        for neg_word in self.negation_words:
            text = re.sub(r'\b' + neg_word + r'\b', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _calculate_consistency_score(
        self,
        total_directives: int,
        contradictions: List[Contradiction]
    ) -> float:
        """
        Calculate overall consistency score (0-10, higher = more consistent).

        Approach:
        - Start with 10 (perfect consistency)
        - Subtract penalties for contradictions based on severity
        """
        score = 10.0

        for contradiction in contradictions:
            if contradiction.severity == ContradictionSeverity.CRITICAL:
                score -= 2.5
            elif contradiction.severity == ContradictionSeverity.HIGH:
                score -= 1.5
            elif contradiction.severity == ContradictionSeverity.MODERATE:
                score -= 0.8
            elif contradiction.severity == ContradictionSeverity.LOW:
                score -= 0.3

        # Normalize by number of directives (more directives = more chances for conflict)
        if total_directives > 10:
            score += (total_directives - 10) * 0.05  # Small bonus for managing complexity

        return max(0.0, min(10.0, score))


def print_contradiction_analysis(analysis: ContradictionAnalysis):
    """Pretty print contradiction analysis results"""
    print("\n" + "="*70)
    print("CONTRADICTION ANALYSIS")
    print("="*70)

    print(f"\nTotal Directives Analyzed: {analysis.total_directives}")
    print(f"Contradictions Found: {len(analysis.contradictions)}")
    print(f"  - CRITICAL: {analysis.critical_count}")
    print(f"  - HIGH: {analysis.high_count}")
    print(f"  - MODERATE: {analysis.moderate_count}")
    print(f"  - LOW: {analysis.low_count}")

    print(f"\nOverall Consistency Score: {analysis.overall_consistency_score:.1f}/10")

    if analysis.overall_consistency_score >= 8.0:
        print("Interpretation: Excellent - No significant contradictions")
    elif analysis.overall_consistency_score >= 6.0:
        print("Interpretation: Good - Minor inconsistencies present")
    elif analysis.overall_consistency_score >= 4.0:
        print("Interpretation: Fair - Some contradictions need resolution")
    else:
        print("Interpretation: Poor - Multiple critical contradictions detected")

    if analysis.contradictions:
        print("\n" + "-"*70)
        print("DETECTED CONTRADICTIONS")
        print("-"*70)

        # Sort by severity
        sorted_contradictions = sorted(
            analysis.contradictions,
            key=lambda c: c.severity.value,
            reverse=True
        )

        for i, contradiction in enumerate(sorted_contradictions, 1):
            print(f"\n{i}. {contradiction}")
    else:
        print("\n[SUCCESS] No contradictions detected - prompt is internally consistent!")

    print("\n" + "="*70)
