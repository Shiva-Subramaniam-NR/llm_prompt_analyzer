"""
Prompt Analysis Framework v2.0
Embedding-Based Semantic Analysis

This module replaces regex-based pattern matching with semantic similarity
using sentence embeddings for more robust and flexible prompt analysis.
"""

from .embedding_manager import EmbeddingManager, EmbeddingConfig
from .synthetic_data import SyntheticDataGenerator, generate_training_data
from .domain_config_v2 import DomainConfigV2, FLIGHT_BOOKING_V2, get_domain_config
from .parameter_detector import SemanticParameterDetector, ParameterMatch, EntityContext
from .vagueness_analyzer import SemanticVaguenessAnalyzer, VaguenessResult
from .analyzer import PromptAnalyzerV2, AnalysisResultV2, quick_analyze

__version__ = "2.0.0"
__all__ = [
    # Main analyzer
    "PromptAnalyzerV2",
    "AnalysisResultV2",
    "quick_analyze",

    # Embedding
    "EmbeddingManager",
    "EmbeddingConfig",

    # Parameter detection
    "SemanticParameterDetector",
    "ParameterMatch",
    "EntityContext",

    # Vagueness analysis
    "SemanticVaguenessAnalyzer",
    "VaguenessResult",

    # Data generation
    "SyntheticDataGenerator",
    "generate_training_data",

    # Domain config
    "DomainConfigV2",
    "FLIGHT_BOOKING_V2",
    "get_domain_config",
]
