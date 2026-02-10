"""
PromptQualityAnalyzer - Master Orchestrator for Prompt Quality Assessment

This is the main entry point for analyzing prompt quality. It coordinates all
sub-components to provide a comprehensive quality report.

Components Integrated:
1. SystemPromptParser - Extracts requirements from system prompts
2. AlignmentChecker - Checks system-user prompt compatibility
3. ContradictionDetector - Finds internal conflicts in prompts
4. VerbosityAnalyzer - Analyzes prompt length and redundancy
5. ObjectiveClassifier - Classifies prompt intent (from v2)
6. SemanticConstraintDetector - Detects semantic constraints (from v2)

Author: Prompt Analysis Framework v2
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import json

from v2.embedding_manager import EmbeddingManager, EmbeddingConfig
from v2.system_prompt_parser import SystemPromptParser, SystemPromptAnalysis
from v2.alignment_checker import AlignmentChecker, AlignmentAnalysis, MisalignmentSeverity
from v2.contradiction_detector import ContradictionDetector, ContradictionAnalysis, ContradictionSeverity
from v2.verbosity_analyzer import VerbosityAnalyzer, VerbosityMetrics
from v2.artifact_handler import ArtifactHandler, Artifact


class PromptQuality(Enum):
    """Overall quality assessment"""
    EXCELLENT = "excellent"      # 9.0-10.0
    GOOD = "good"                # 7.0-8.9
    FAIR = "fair"                # 5.0-6.9
    POOR = "poor"                # 3.0-4.9
    CRITICAL = "critical"        # 0.0-2.9


class RiskLevel(Enum):
    """Risk level for unified scoring"""
    NONE = "none"               # No safety/security risks
    LOW = "low"                 # Minor concerns
    MODERATE = "moderate"       # Needs revision
    HIGH = "high"               # Not recommended
    CRITICAL = "critical"       # Dangerous/illegal


@dataclass
class QualityIssue:
    """Represents a quality issue found during analysis"""
    category: str  # "alignment", "contradiction", "verbosity", etc.
    severity: str  # "critical", "high", "moderate", "low"
    title: str
    description: str
    recommendation: str
    confidence: float = 0.0

    def __repr__(self):
        return (
            f"[{self.severity.upper()}] {self.category.upper()}\n"
            f"  {self.title}\n"
            f"  {self.description}\n"
            f"  Fix: {self.recommendation}"
        )


@dataclass
class PromptQualityReport:
    """Complete quality assessment report"""

    # Overall metrics (REQUIRED)
    overall_score: float  # 0-10
    quality_rating: PromptQuality
    is_fulfillable: bool  # Can system fulfill user request?

    # Individual component scores (REQUIRED)
    alignment_score: float        # 0-10
    consistency_score: float      # 0-10 (from contradiction detection)
    verbosity_score: float        # 0-10 (inverse of verbosity)
    completeness_score: float     # 0-10

    # Unified scoring (OPTIONAL - when Tier 2 is available)
    unified_score: Optional[float] = None  # 0-10, overrides overall_score when Tier 2 detects risks
    unified_verdict: Optional[str] = None  # "RECOMMENDED", "NEEDS REVISION", "NOT RECOMMENDED", "DANGEROUS"
    risk_level: RiskLevel = RiskLevel.NONE
    primary_concern: Optional[str] = None  # Main issue detected by Tier 2
    tier1_explanation: str = "Measures prompt structure, format, and internal consistency. Does NOT evaluate ethical/safety concerns."
    tier2_explanation: Optional[str] = None  # Explanation when Tier 2 is used

    # Detailed results from each component
    system_analysis: Optional[SystemPromptAnalysis] = None
    alignment_analysis: Optional[AlignmentAnalysis] = None
    contradiction_analysis: Optional[ContradictionAnalysis] = None
    verbosity_metrics: Optional[VerbosityMetrics] = None

    # Aggregated issues
    all_issues: List[QualityIssue] = field(default_factory=list)
    critical_issues: List[QualityIssue] = field(default_factory=list)
    high_issues: List[QualityIssue] = field(default_factory=list)
    moderate_issues: List[QualityIssue] = field(default_factory=list)
    low_issues: List[QualityIssue] = field(default_factory=list)

    # Summary statistics
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    moderate_count: int = 0
    low_count: int = 0

    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization"""
        return {
            "overall_score": round(self.overall_score, 2),
            "quality_rating": self.quality_rating.value,
            "is_fulfillable": self.is_fulfillable,
            "scores": {
                "alignment": round(self.alignment_score, 2),
                "consistency": round(self.consistency_score, 2),
                "verbosity": round(self.verbosity_score, 2),
                "completeness": round(self.completeness_score, 2)
            },
            "issue_counts": {
                "total": self.total_issues,
                "critical": self.critical_count,
                "high": self.high_count,
                "moderate": self.moderate_count,
                "low": self.low_count
            },
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "title": issue.title,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "confidence": round(issue.confidence, 2)
                }
                for issue in self.all_issues
            ]
        }

    def to_json(self, indent: int = 2) -> str:
        """Export report as JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, filepath: str):
        """Save report to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


class PromptQualityAnalyzer:
    """
    Master orchestrator for comprehensive prompt quality analysis.

    This is the main entry point for developers using this framework.

    Usage:
        analyzer = PromptQualityAnalyzer()

        report = analyzer.analyze(
            system_prompt="You are a flight booking assistant...",
            user_prompt="Book me a flight from NYC to London"
        )

        print(f"Overall Score: {report.overall_score}/10")
        print(f"Quality: {report.quality_rating.value}")
        print(f"Issues Found: {report.total_issues}")
    """

    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize the analyzer with all sub-components.

        Args:
            embedding_config: Configuration for embedding model
            verbose: Print progress messages
        """
        self.verbose = verbose

        # Initialize embedding manager
        if embedding_config is None:
            embedding_config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")

        if self.verbose:
            print("[INFO] Initializing Prompt Quality Analyzer...")

        self.embedding_manager = EmbeddingManager(embedding_config)

        # Initialize all sub-components
        self.system_prompt_parser = SystemPromptParser(self.embedding_manager)
        self.alignment_checker = AlignmentChecker(
            self.embedding_manager,
            self.system_prompt_parser
        )
        self.contradiction_detector = ContradictionDetector(self.embedding_manager)
        self.verbosity_analyzer = VerbosityAnalyzer(self.embedding_manager)
        self.artifact_handler = ArtifactHandler()

        if self.verbose:
            print("[OK] All components initialized successfully")

    def analyze(
        self,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        artifacts: Optional[Dict[str, str]] = None
    ) -> PromptQualityReport:
        """
        Perform comprehensive quality analysis on prompts.

        Args:
            system_prompt: The system prompt to analyze
            user_prompt: Optional user prompt for alignment checking
            artifacts: Optional dict of artifact names to file paths
                      e.g., {'document': 'path/to/doc.pdf', 'image': 'path/to/img.jpg'}

        Returns:
            PromptQualityReport with detailed analysis
        """
        if self.verbose:
            print("\n[ANALYZING] Running comprehensive quality analysis...")

        # 0. Process artifacts (if provided)
        processed_artifacts = {}
        artifact_issues = []
        if artifacts:
            if self.verbose:
                print("  [0/5] Processing artifacts...")
            processed_artifacts, artifact_issues = self.artifact_handler.process_artifacts(artifacts)

            # Check if artifacts mentioned in prompts are provided
            if user_prompt:
                mention_issues = self.artifact_handler.validate_artifacts_mentioned_in_prompt(
                    user_prompt, processed_artifacts
                )
                artifact_issues.extend(mention_issues)

            if self.verbose and artifact_issues:
                print(f"       Found {len(artifact_issues)} artifact issues")

        # 1. Parse system prompt
        if self.verbose:
            print(f"  [1/{5 if artifacts else 4}] Parsing system prompt...")
        system_analysis = self.system_prompt_parser.parse(system_prompt)

        # 2. Check for contradictions in system prompt
        if self.verbose:
            print(f"  [2/{5 if artifacts else 4}] Detecting contradictions...")
        contradiction_analysis = self.contradiction_detector.detect(system_prompt)

        # 3. Analyze verbosity
        if self.verbose:
            print(f"  [3/{5 if artifacts else 4}] Analyzing verbosity...")
        verbosity_metrics = self.verbosity_analyzer.analyze(system_prompt)

        # 4. Check alignment (if user prompt provided)
        alignment_analysis = None
        if user_prompt:
            if self.verbose:
                print(f"  [4/{5 if artifacts else 4}] Checking alignment with user prompt...")
            alignment_analysis = self.alignment_checker.check_alignment(
                system_prompt, user_prompt
            )
        else:
            if self.verbose:
                print(f"  [4/{5 if artifacts else 4}] Skipping alignment check (no user prompt)")

        # Aggregate results
        report = self._create_report(
            system_analysis,
            contradiction_analysis,
            verbosity_metrics,
            alignment_analysis,
            processed_artifacts,
            artifact_issues
        )

        if self.verbose:
            print(f"[COMPLETE] Analysis finished. Overall Score: {report.overall_score:.1f}/10")

        return report

    def calculate_unified_score(
        self,
        report: PromptQualityReport,
        tier2_result=None
    ) -> PromptQualityReport:
        """
        Calculate unified score when Tier 2 analysis is available.

        Logic:
        - If Tier 2 detects SAFETY or SECURITY risks: Override Tier 1 completely
        - If Tier 2 detects SEMANTIC impossibility: Blend scores (30% Tier 1, 70% Tier 2)
        - Otherwise: Use Tier 1 score as-is

        Args:
            report: The original Tier 1 report
            tier2_result: SemanticImpossibilityResult from LLM analysis

        Returns:
            Updated report with unified scoring
        """
        print(f"[DEBUG] calculate_unified_score called. tier2_result={tier2_result is not None}")
        if tier2_result:
            print(f"[DEBUG] is_impossible={tier2_result.is_impossible}, risk_type={tier2_result.primary_risk_type}")

        if not tier2_result:
            # No Tier 2, return original report
            print("[DEBUG] No tier2_result, returning original report")
            return report

        tier1_score = report.overall_score

        # Determine risk level and unified score based on Tier 2 results
        if tier2_result.is_impossible:
            risk_type = tier2_result.primary_risk_type.lower()
            impossibility_score = tier2_result.impossibility_score  # 0-10, higher = more risky

            if risk_type == 'safety':
                # CRITICAL: Safety violations override everything
                unified_score = max(0, 10 - impossibility_score)  # Invert: high risk = low score

                if impossibility_score >= 9.0:
                    risk_level = RiskLevel.CRITICAL
                    verdict = "DANGEROUS - REJECT IMMEDIATELY"
                elif impossibility_score >= 7.0:
                    risk_level = RiskLevel.HIGH
                    verdict = "HIGH RISK - NOT RECOMMENDED"
                else:
                    risk_level = RiskLevel.MODERATE
                    verdict = "SAFETY CONCERNS - NEEDS REVISION"

                primary_concern = f"Safety Violation: {tier2_result.explanation[:200]}"

            elif risk_type == 'security':
                # HIGH: Security issues override Tier 1
                unified_score = max(0, 10 - impossibility_score)

                if impossibility_score >= 8.0:
                    risk_level = RiskLevel.CRITICAL
                    verdict = "CRITICAL SECURITY RISK - REJECT"
                elif impossibility_score >= 6.0:
                    risk_level = RiskLevel.HIGH
                    verdict = "SECURITY RISK - NOT RECOMMENDED"
                else:
                    risk_level = RiskLevel.MODERATE
                    verdict = "SECURITY CONCERNS - NEEDS REVISION"

                primary_concern = f"Security Risk: {tier2_result.explanation[:200]}"

            else:  # semantic impossibility
                # MODERATE: Blend Tier 1 (structure) + Tier 2 (semantics)
                tier2_score = 10 - impossibility_score  # Invert
                unified_score = (0.3 * tier1_score) + (0.7 * tier2_score)

                if impossibility_score >= 7.0:
                    risk_level = RiskLevel.HIGH
                    verdict = "SEMANTICALLY IMPOSSIBLE - REVISE REQUEST"
                elif impossibility_score >= 4.0:
                    risk_level = RiskLevel.MODERATE
                    verdict = "NEEDS REVISION"
                else:
                    risk_level = RiskLevel.LOW
                    verdict = "MINOR CONCERNS"

                primary_concern = f"Semantic Issue: {tier2_result.explanation[:200]}"

        else:
            # Tier 2 says it's fulfillable - use Tier 1 score with boost
            unified_score = min(10.0, tier1_score + 0.5)  # Small boost for passing Tier 2
            risk_level = RiskLevel.NONE
            verdict = "RECOMMENDED" if unified_score >= 7.0 else "ACCEPTABLE"
            primary_concern = None

        # Update report with unified scoring
        report.unified_score = unified_score
        report.unified_verdict = verdict
        report.risk_level = risk_level
        report.primary_concern = primary_concern
        report.tier2_explanation = (
            "Uses AI to detect illegal requests, safety risks, prompt injection attacks, "
            "and semantic impossibility. When risks are detected, Tier 2 overrides Tier 1."
        )

        return report

    def _create_report(
        self,
        system_analysis: SystemPromptAnalysis,
        contradiction_analysis: ContradictionAnalysis,
        verbosity_metrics: VerbosityMetrics,
        alignment_analysis: Optional[AlignmentAnalysis],
        processed_artifacts: Optional[Dict[str, Artifact]] = None,
        artifact_issues: Optional[List[str]] = None
    ) -> PromptQualityReport:
        """Aggregate results from all components into a unified report"""

        all_issues = []

        # Add artifact issues first (if any)
        if artifact_issues:
            for artifact_issue in artifact_issues:
                issue = QualityIssue(
                    category="artifact",
                    severity="high",
                    title="Artifact Issue",
                    description=artifact_issue,
                    recommendation="Ensure all mentioned artifacts are provided and accessible",
                    confidence=1.0
                )
                all_issues.append(issue)

        # Extract issues from contradiction analysis
        for contradiction in contradiction_analysis.contradictions:
            severity_map = {
                ContradictionSeverity.CRITICAL: "critical",
                ContradictionSeverity.HIGH: "high",
                ContradictionSeverity.MODERATE: "moderate",
                ContradictionSeverity.LOW: "low"
            }

            issue = QualityIssue(
                category="contradiction",
                severity=severity_map[contradiction.severity],
                title=f"{contradiction.type.value.replace('_', ' ').title()}",
                description=contradiction.explanation,
                recommendation=f"Resolve conflict between:\n  - \"{contradiction.statement1[:60]}...\"\n  - \"{contradiction.statement2[:60]}...\"",
                confidence=contradiction.confidence
            )
            all_issues.append(issue)

        # Extract issues from verbosity analysis
        if verbosity_metrics.verbosity_score > 5.0:
            issue = QualityIssue(
                category="verbosity",
                severity="moderate" if verbosity_metrics.verbosity_score < 7.0 else "high",
                title="Prompt is too verbose",
                description=f"Prompt contains {verbosity_metrics.total_words} words. Optimal range: 50-150 words.",
                recommendation="Reduce word count by removing redundant phrases and consolidating directives.",
                confidence=0.90
            )
            all_issues.append(issue)

        if verbosity_metrics.buried_directives:
            issue = QualityIssue(
                category="verbosity",
                severity="high",
                title=f"Critical directives buried deep in prompt",
                description=f"Found {len(verbosity_metrics.buried_directives)} critical directives after word 100",
                recommendation="Move MUST/NEVER directives to the beginning of the prompt for better visibility.",
                confidence=0.95
            )
            all_issues.append(issue)

        if verbosity_metrics.redundancy_score > 6.0:
            issue = QualityIssue(
                category="verbosity",
                severity="moderate",
                title="High redundancy detected",
                description=f"Redundancy score: {verbosity_metrics.redundancy_score:.1f}/10",
                recommendation="Remove repeated phrases and consolidate similar directives.",
                confidence=0.85
            )
            all_issues.append(issue)

        # Extract issues from alignment analysis (if available)
        if alignment_analysis:
            for misalignment in alignment_analysis.misalignments:
                severity_map = {
                    MisalignmentSeverity.CRITICAL: "critical",
                    MisalignmentSeverity.HIGH: "high",
                    MisalignmentSeverity.MODERATE: "moderate",
                    MisalignmentSeverity.LOW: "low"
                }

                issue = QualityIssue(
                    category="alignment",
                    severity=severity_map[misalignment.severity],
                    title=misalignment.type.value.replace('_', ' ').title(),
                    description=misalignment.description,
                    recommendation=misalignment.recommendation,
                    confidence=misalignment.confidence
                )
                all_issues.append(issue)

        # Categorize issues by severity
        critical_issues = [i for i in all_issues if i.severity == "critical"]
        high_issues = [i for i in all_issues if i.severity == "high"]
        moderate_issues = [i for i in all_issues if i.severity == "moderate"]
        low_issues = [i for i in all_issues if i.severity == "low"]

        # Calculate individual scores
        consistency_score = contradiction_analysis.overall_consistency_score

        # Verbosity score (inverse - lower verbosity = higher score)
        verbosity_score = max(0.0, 10.0 - verbosity_metrics.verbosity_score)

        # Alignment score (if available)
        if alignment_analysis:
            alignment_score = alignment_analysis.alignment_score.overall_score
            completeness_score = alignment_analysis.alignment_score.completeness
            is_fulfillable = alignment_analysis.is_fulfillable()
        else:
            alignment_score = 10.0  # No user prompt, assume perfect alignment
            completeness_score = 10.0
            is_fulfillable = True

        # Calculate overall score (weighted average)
        if alignment_analysis:
            # With user prompt: all factors matter
            overall_score = (
                0.30 * alignment_score +
                0.25 * consistency_score +
                0.25 * completeness_score +
                0.20 * verbosity_score
            )
        else:
            # Without user prompt: focus on system prompt quality
            overall_score = (
                0.50 * consistency_score +
                0.50 * verbosity_score
            )

        # Determine quality rating
        if overall_score >= 9.0:
            quality_rating = PromptQuality.EXCELLENT
        elif overall_score >= 7.0:
            quality_rating = PromptQuality.GOOD
        elif overall_score >= 5.0:
            quality_rating = PromptQuality.FAIR
        elif overall_score >= 3.0:
            quality_rating = PromptQuality.POOR
        else:
            quality_rating = PromptQuality.CRITICAL

        return PromptQualityReport(
            overall_score=overall_score,
            quality_rating=quality_rating,
            is_fulfillable=is_fulfillable,
            alignment_score=alignment_score,
            consistency_score=consistency_score,
            verbosity_score=verbosity_score,
            completeness_score=completeness_score,
            system_analysis=system_analysis,
            alignment_analysis=alignment_analysis,
            contradiction_analysis=contradiction_analysis,
            verbosity_metrics=verbosity_metrics,
            all_issues=all_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            moderate_issues=moderate_issues,
            low_issues=low_issues,
            total_issues=len(all_issues),
            critical_count=len(critical_issues),
            high_count=len(high_issues),
            moderate_count=len(moderate_issues),
            low_count=len(low_issues)
        )


def print_quality_report(report: PromptQualityReport):
    """Pretty print the quality report"""
    print("\n" + "="*70)
    print("PROMPT QUALITY ANALYSIS REPORT")
    print("="*70)

    # Overall metrics
    print(f"\nOVERALL SCORE: {report.overall_score:.1f}/10")
    print(f"QUALITY RATING: {report.quality_rating.value.upper()}")
    print(f"CAN FULFILL REQUEST: {'YES' if report.is_fulfillable else 'NO'}")

    # Individual scores
    print(f"\n{'='*70}")
    print("COMPONENT SCORES")
    print(f"{'='*70}")
    print(f"  Alignment:    {report.alignment_score:.1f}/10")
    print(f"  Consistency:  {report.consistency_score:.1f}/10")
    print(f"  Verbosity:    {report.verbosity_score:.1f}/10")
    print(f"  Completeness: {report.completeness_score:.1f}/10")

    # Issue summary
    print(f"\n{'='*70}")
    print(f"ISSUES FOUND: {report.total_issues}")
    print(f"{'='*70}")
    print(f"  CRITICAL: {report.critical_count}")
    print(f"  HIGH:     {report.high_count}")
    print(f"  MODERATE: {report.moderate_count}")
    print(f"  LOW:      {report.low_count}")

    # Detailed issues
    if report.all_issues:
        print(f"\n{'='*70}")
        print("DETAILED ISSUES")
        print(f"{'='*70}")

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
        sorted_issues = sorted(report.all_issues, key=lambda i: severity_order[i.severity])

        for i, issue in enumerate(sorted_issues, 1):
            print(f"\n{i}. {issue}")
    else:
        print(f"\n[PERFECT] No issues detected!")

    print("\n" + "="*70)
