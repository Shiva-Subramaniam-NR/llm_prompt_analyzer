"""
Semantic Vagueness Analyzer v2.0

Calculates vagueness scores using embedding-based specificity measurement.
Uses pre-trained specificity clusters to determine how specific/vague values are.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .embedding_manager import EmbeddingManager, softmax
from .domain_config_v2 import DomainConfigV2
from .parameter_detector import ParameterMatch
from .synthetic_data import generate_training_data


@dataclass
class VaguenessResult:
    """Complete vagueness analysis result"""
    score: float
    interpretation: str
    completeness_score: float
    specificity_score: float
    missing_params: List[str]
    param_specificity: Dict[str, float]
    suggested_followups: List[str]


class SemanticVaguenessAnalyzer:
    """
    Analyzes vagueness using semantic similarity to specificity clusters.

    Process:
    1. Generate synthetic data for specificity levels
    2. Compute centroids for specific/moderate/vague clusters
    3. For each detected value, measure distance to clusters
    4. Combine with completeness for final vagueness score
    """

    # Follow-up question templates
    FOLLOWUP_TEMPLATES = {
        "origin": "Where will you be departing from?",
        "destination": "Where do you want to go?",
        "date_outbound": "What date would you like to travel?",
        "date_return": "When would you like to return?",
        "time_preference": "What time of day do you prefer to fly?",
        "class": "Which cabin class do you prefer? (Economy/Business/First)",
        "budget": "What is your maximum budget for this trip?"
    }

    VAGUE_FOLLOWUPS = {
        "date": "Can you provide a specific date instead of '{value}'?",
        "time": "Can you specify an exact time or time range instead of '{value}'?",
        "budget": "Can you give a specific amount instead of '{value}'?"
    }

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        domain: DomainConfigV2,
        samples_per_category: int = 100
    ):
        """
        Initialize analyzer with embedding manager.

        Args:
            embedding_manager: Pre-configured embedding manager
            domain: Domain configuration
            samples_per_category: Samples for synthetic data generation
        """
        self.embeddings = embedding_manager
        self.domain = domain
        self.samples_per_category = samples_per_category
        self._centroids_computed = False

    def _ensure_centroids(self):
        """Ensure specificity centroids are computed"""
        if self._centroids_computed:
            return

        print("[INFO] Generating synthetic training data...")
        training_data = generate_training_data(self.samples_per_category)

        print("[INFO] Computing specificity centroids...")
        self.embeddings.precompute_specificity_centroids(training_data)
        self._centroids_computed = True
        print("[OK] Specificity centroids ready")

    def analyze(
        self,
        detected_params: Dict[str, ParameterMatch],
        prompt: str
    ) -> VaguenessResult:
        """
        Perform complete vagueness analysis.

        Args:
            detected_params: Parameters detected by SemanticParameterDetector
            prompt: Original prompt text

        Returns:
            VaguenessResult with scores and recommendations
        """
        self._ensure_centroids()

        # 1. Calculate completeness score
        completeness_score, missing_params = self._calculate_completeness(detected_params)

        # 2. Calculate specificity for each detected parameter
        param_specificity = {}
        for param_name, match in detected_params.items():
            specificity_type = self.domain.param_specificity_type.get(param_name)
            if specificity_type in ["date", "time", "budget"]:
                spec = self._calculate_specificity(match.value, specificity_type)
            else:
                # Locations and classes are generally specific if detected
                spec = 0.85 if match.confidence > 0.7 else 0.6
            param_specificity[param_name] = spec

        # 3. Calculate average specificity score
        if param_specificity:
            avg_specificity = np.mean(list(param_specificity.values()))
        else:
            avg_specificity = 0.0  # No params detected = can't assess specificity

        # Convert to vagueness scale (0 = specific, 10 = vague)
        specificity_score = 10 * (1 - avg_specificity)

        # 4. Combine scores using weights
        weights = self.domain.weights
        vagueness_score = (
            weights["completeness"] * completeness_score +
            weights["specificity"] * specificity_score
        )

        # 5. Apply critical parameter penalty
        vagueness_score = self._apply_critical_penalty(missing_params, vagueness_score)

        # 6. Generate follow-up questions
        followups = self._generate_followups(missing_params, param_specificity, detected_params)

        # 7. Get interpretation
        interpretation = self._interpret(vagueness_score)

        return VaguenessResult(
            score=round(vagueness_score, 1),
            interpretation=interpretation,
            completeness_score=round(completeness_score, 1),
            specificity_score=round(specificity_score, 1),
            missing_params=missing_params,
            param_specificity={k: round(v, 2) for k, v in param_specificity.items()},
            suggested_followups=followups
        )

    def _calculate_completeness(
        self,
        detected_params: Dict[str, ParameterMatch]
    ) -> Tuple[float, List[str]]:
        """
        Calculate completeness score based on missing parameters.

        Uses exponential penalty: 10 × (missing_ratio)^0.7
        """
        all_params = set(self.domain.parameter_anchors.keys())
        # date_return is optional
        required_params = all_params - {"date_return"}

        detected = set(detected_params.keys())
        missing = list(required_params - detected)

        total = len(required_params)
        missing_count = len(missing)

        if missing_count == 0:
            return 0.0, []

        # Exponential penalty
        missing_ratio = missing_count / total
        score = 10 * (missing_ratio ** 0.7)

        return min(score, 10.0), missing

    def _calculate_specificity(self, value: str, param_type: str) -> float:
        """
        Calculate specificity score (0-1) using centroid distances.

        Returns:
            1.0 = very specific, 0.0 = very vague
        """
        centroids = self.embeddings.get_specificity_centroids(param_type)
        if not centroids:
            return 0.5  # Unknown type, assume moderate

        # Embed the value
        value_embedding = self.embeddings.encode(value)

        # Calculate similarity to each specificity level centroid
        similarities = {}
        for level, centroid in centroids.items():
            sim = self.embeddings.cosine_similarity(value_embedding, centroid)
            similarities[level] = sim

        # Use softmax to get probability distribution
        # Higher similarity = higher probability of being that level
        levels = ["specific", "moderate", "vague"]
        sim_array = np.array([similarities.get(l, 0) for l in levels])

        # Apply temperature to sharpen distribution
        temperature = 0.5
        probs = softmax(sim_array / temperature)

        # Weighted specificity score
        # specific=1.0, moderate=0.5, vague=0.0
        specificity = probs[0] * 1.0 + probs[1] * 0.5 + probs[2] * 0.0

        return float(specificity)

    def _apply_critical_penalty(
        self,
        missing_params: List[str],
        base_score: float
    ) -> float:
        """Apply extra penalty for missing critical parameters"""
        penalty = 0.0

        critical_missing = [p for p in missing_params if self.domain.is_critical(p)]

        # Both origin and destination missing = catastrophic
        if "origin" in missing_params and "destination" in missing_params:
            penalty += 2.0
        elif "origin" in missing_params or "destination" in missing_params:
            penalty += 1.0

        # Date missing
        if "date_outbound" in missing_params:
            penalty += 0.5

        return min(base_score + penalty, 10.0)

    def _generate_followups(
        self,
        missing_params: List[str],
        param_specificity: Dict[str, float],
        detected_params: Dict[str, ParameterMatch]
    ) -> List[str]:
        """Generate follow-up questions for missing/vague parameters"""
        followups = []

        # Questions for missing parameters
        for param in missing_params:
            if param in self.FOLLOWUP_TEMPLATES:
                followups.append(self.FOLLOWUP_TEMPLATES[param])

        # Questions for vague parameters (specificity < 0.5)
        for param, specificity in param_specificity.items():
            if specificity < 0.5:
                param_type = self.domain.param_specificity_type.get(param)
                if param_type in self.VAGUE_FOLLOWUPS:
                    value = detected_params[param].value
                    followups.append(
                        self.VAGUE_FOLLOWUPS[param_type].format(value=value)
                    )

        return followups

    def _interpret(self, score: float) -> str:
        """Get human-readable interpretation of vagueness score"""
        if score <= 1.5:
            return "Very Specific - Ready for execution"
        elif score <= 3.5:
            return "Mostly Specific - Minor clarifications may help"
        elif score <= 5.5:
            return "Moderate Vagueness - Follow-ups recommended"
        elif score <= 7.5:
            return "High Vagueness - Significant clarification needed"
        else:
            return "Extremely Vague - Cannot execute without clarification"


class SpecificityClusterTrainer:
    """
    Trains specificity clusters from synthetic data.

    This is an alternative approach using K-means clustering
    instead of pre-defined centroids.
    """

    def __init__(self, embedding_manager: EmbeddingManager):
        self.embeddings = embedding_manager
        self.clusters = {}

    def train(self, training_data: Dict[str, Dict[str, List[str]]]):
        """
        Train clusters for each parameter type.

        Args:
            training_data: Dict[param_type][level] = list of examples
        """
        from sklearn.cluster import KMeans

        for param_type, levels in training_data.items():
            # Combine all examples with labels
            all_examples = []
            all_labels = []
            for level, examples in levels.items():
                all_examples.extend(examples)
                all_labels.extend([level] * len(examples))

            # Embed all examples
            embeddings = self.embeddings.encode_batch(all_examples)

            # Train K-means with k=3 (specific, moderate, vague)
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)

            # Map clusters to specificity levels based on label distribution
            cluster_to_level = self._map_clusters_to_levels(
                cluster_labels, all_labels
            )

            self.clusters[param_type] = {
                "model": kmeans,
                "mapping": cluster_to_level
            }

    def _map_clusters_to_levels(
        self,
        cluster_labels: np.ndarray,
        true_labels: List[str]
    ) -> Dict[int, str]:
        """Map cluster indices to specificity levels"""
        from collections import Counter

        cluster_level_counts = {}
        for cluster_id, true_label in zip(cluster_labels, true_labels):
            if cluster_id not in cluster_level_counts:
                cluster_level_counts[cluster_id] = Counter()
            cluster_level_counts[cluster_id][true_label] += 1

        # Assign each cluster to its most common label
        mapping = {}
        assigned_levels = set()
        for cluster_id, counts in cluster_level_counts.items():
            # Find most common label not yet assigned
            for level, _ in counts.most_common():
                if level not in assigned_levels:
                    mapping[cluster_id] = level
                    assigned_levels.add(level)
                    break

        return mapping

    def predict_specificity(self, value: str, param_type: str) -> float:
        """Predict specificity score using trained clusters"""
        if param_type not in self.clusters:
            return 0.5

        cluster_info = self.clusters[param_type]
        embedding = self.embeddings.encode(value).reshape(1, -1)

        # Get distances to all centroids
        distances = cluster_info["model"].transform(embedding)[0]

        # Convert to probabilities (inverse distance)
        inv_distances = 1 / (distances + 1e-6)
        probs = inv_distances / inv_distances.sum()

        # Calculate weighted specificity
        specificity = 0.0
        level_weights = {"specific": 1.0, "moderate": 0.5, "vague": 0.0}

        for cluster_id, level in cluster_info["mapping"].items():
            specificity += probs[cluster_id] * level_weights.get(level, 0.5)

        return float(specificity)
