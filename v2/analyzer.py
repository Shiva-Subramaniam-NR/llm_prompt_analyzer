"""
Prompt Analyzer v2.0

Main orchestrator for embedding-based prompt analysis.
Combines parameter detection and vagueness analysis.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .embedding_manager import EmbeddingManager, EmbeddingConfig
from .domain_config_v2 import DomainConfigV2, get_domain_config
from .parameter_detector import SemanticParameterDetector, ParameterMatch
from .vagueness_analyzer import SemanticVaguenessAnalyzer, VaguenessResult


@dataclass
class AnalysisResultV2:
    """Complete analysis result"""
    prompt: str
    detected_parameters: Dict[str, Dict]
    vagueness: Dict
    high_weightage_words: List[Dict]  # For backward compatibility

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "prompt": self.prompt,
            "detected_parameters": self.detected_parameters,
            "vagueness_analysis": self.vagueness,
            "high_weightage_words": self.high_weightage_words
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class PromptAnalyzerV2:
    """
    Embedding-based prompt analyzer.

    Replaces regex pattern matching with semantic similarity
    for more robust and flexible analysis.
    """

    def __init__(
        self,
        domain: str = "flight_booking",
        model_name: str = "all-MiniLM-L6-v2",
        precompute_path: Optional[str] = None
    ):
        """
        Initialize analyzer.

        Args:
            domain: Domain name (e.g., "flight_booking")
            model_name: Sentence transformer model name
            precompute_path: Path to load/save pre-computed embeddings
        """
        self.domain_name = domain
        self.domain_config = get_domain_config(domain)

        # Initialize embedding manager
        config = EmbeddingConfig(model_name=model_name)
        self.embedding_manager = EmbeddingManager(config)

        # Try to load pre-computed embeddings
        if precompute_path and self.embedding_manager.load_precomputed(precompute_path):
            print(f"[OK] Loaded pre-computed embeddings from {precompute_path}")
        else:
            # Pre-compute anchor embeddings
            self.embedding_manager.precompute_anchors(
                self.domain_config.parameter_anchors
            )
            if precompute_path:
                self.embedding_manager.save_precomputed(precompute_path)

        # Initialize components
        self.param_detector = SemanticParameterDetector(
            self.embedding_manager,
            self.domain_config
        )

        self.vagueness_analyzer = SemanticVaguenessAnalyzer(
            self.embedding_manager,
            self.domain_config
        )

        print(f"[OK] PromptAnalyzerV2 initialized for domain: {domain}")

    def analyze(self, prompt: str) -> AnalysisResultV2:
        """
        Analyze a prompt.

        Args:
            prompt: Input prompt text

        Returns:
            AnalysisResultV2 with detected parameters and vagueness score
        """
        # Step 1: Detect parameters
        detected_params = self.param_detector.detect(prompt)

        # Step 2: Analyze vagueness
        vagueness = self.vagueness_analyzer.analyze(detected_params, prompt)

        # Step 3: Extract high-weightage words (for backward compatibility)
        high_weightage = self._extract_high_weightage(detected_params)

        # Convert to serializable format
        params_dict = {
            name: {
                "value": match.value,
                "confidence": round(match.confidence, 2),
                "method": match.method
            }
            for name, match in detected_params.items()
        }

        vagueness_dict = {
            "vagueness_score": vagueness.score,
            "interpretation": vagueness.interpretation,
            "completeness_score": vagueness.completeness_score,
            "specificity_score": vagueness.specificity_score,
            "missing_params": vagueness.missing_params,
            "param_specificity": vagueness.param_specificity,
            "suggested_followups": vagueness.suggested_followups
        }

        return AnalysisResultV2(
            prompt=prompt,
            detected_parameters=params_dict,
            vagueness=vagueness_dict,
            high_weightage_words=high_weightage
        )

    def _extract_high_weightage(
        self,
        detected_params: Dict[str, ParameterMatch]
    ) -> List[Dict]:
        """Extract high-weightage words for backward compatibility"""
        words = []

        for param_name, match in detected_params.items():
            # Use confidence as proxy for weightage
            if match.confidence >= 0.6:
                words.append({
                    "text": match.value,
                    "weightage": round(match.confidence, 2),
                    "type": param_name,
                    "method": match.method
                })

        return words

    def analyze_and_print(self, prompt: str) -> Dict:
        """
        Analyze prompt and print formatted results.

        Args:
            prompt: Input prompt text

        Returns:
            Analysis result as dictionary
        """
        result = self.analyze(prompt)

        print("\n" + "=" * 70)
        print("PROMPT ANALYSIS (v2.0 - Embedding-Based)")
        print("=" * 70)
        print(f"\nPrompt: {prompt}")

        print("\n--- Detected Parameters ---")
        if result.detected_parameters:
            for param, info in result.detected_parameters.items():
                conf_bar = "█" * int(info["confidence"] * 10)
                print(f"  {param}: {info['value']}")
                print(f"    Confidence: {info['confidence']:.2f} [{conf_bar}]")
                print(f"    Method: {info['method']}")
        else:
            print("  No parameters detected")

        print("\n--- Vagueness Analysis ---")
        v = result.vagueness
        print(f"  Score: {v['vagueness_score']}/10")
        print(f"  Interpretation: {v['interpretation']}")
        print(f"  Completeness Score: {v['completeness_score']}/10")
        print(f"  Specificity Score: {v['specificity_score']}/10")

        if v["missing_params"]:
            print(f"\n  Missing Parameters: {', '.join(v['missing_params'])}")

        if v["param_specificity"]:
            print("\n  Parameter Specificity:")
            for param, spec in v["param_specificity"].items():
                spec_bar = "█" * int(spec * 10)
                label = "specific" if spec > 0.7 else "moderate" if spec > 0.4 else "vague"
                print(f"    {param}: {spec:.2f} [{spec_bar}] ({label})")

        if v["suggested_followups"]:
            print("\n  Suggested Follow-ups:")
            for q in v["suggested_followups"]:
                print(f"    • {q}")

        print("\n" + "=" * 70)

        return result.to_dict()


def quick_analyze(prompt: str, domain: str = "flight_booking") -> Dict:
    """
    Quick analysis function for one-off use.

    Args:
        prompt: Input prompt
        domain: Domain name

    Returns:
        Analysis result dictionary
    """
    analyzer = PromptAnalyzerV2(domain=domain)
    return analyzer.analyze(prompt).to_dict()
