"""
Prompt Analysis Framework v2.0
Embedding-Based Semantic Analysis

This module provides embedding-based prompt quality analysis with
optional LLM deep analysis (Phase 2).
"""

from .embedding_manager import EmbeddingManager, EmbeddingConfig
from .prompt_quality_analyzer import PromptQualityAnalyzer, PromptQualityReport, QualityIssue
from .system_prompt_parser import SystemPromptParser, SystemPromptAnalysis
from .alignment_checker import AlignmentChecker, AlignmentAnalysis
from .contradiction_detector import ContradictionDetector, ContradictionAnalysis
from .verbosity_analyzer import VerbosityAnalyzer, VerbosityMetrics
from .artifact_handler import ArtifactHandler, Artifact, ArtifactType

# Phase 2 - Optional LLM integration
try:
    from .llm_analyzer import LLMAnalyzer, SemanticImpossibilityResult, LLMExplanation
    __llm_available__ = True
except ImportError:
    __llm_available__ = False

__version__ = "2.1.0"  # Phase 2
__all__ = [
    # Main orchestrator
    "PromptQualityAnalyzer",
    "PromptQualityReport",
    "QualityIssue",

    # Embedding
    "EmbeddingManager",
    "EmbeddingConfig",

    # Components
    "SystemPromptParser",
    "SystemPromptAnalysis",
    "AlignmentChecker",
    "AlignmentAnalysis",
    "ContradictionDetector",
    "ContradictionAnalysis",
    "VerbosityAnalyzer",
    "VerbosityMetrics",

    # Artifacts (Phase 1)
    "ArtifactHandler",
    "Artifact",
    "ArtifactType",

    # LLM (Phase 2 - optional)
    "LLMAnalyzer",
    "SemanticImpossibilityResult",
    "LLMExplanation",
]
