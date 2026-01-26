"""
Embedding Manager v2.0

Handles all embedding operations using Sentence Transformers.
Provides caching, batch processing, and pre-computed anchor embeddings.
"""

import numpy as np
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import os
import pickle


@dataclass
class EmbeddingConfig:
    """Configuration for embedding manager"""
    model_name: str = "all-MiniLM-L6-v2"
    cache_dir: Optional[str] = None
    normalize: bool = True
    device: str = "cpu"  # "cpu" or "cuda"


class EmbeddingManager:
    """
    Manages embedding model and provides efficient embedding operations.

    Features:
    - Lazy model loading
    - Embedding caching
    - Batch processing
    - Pre-computed anchor embeddings
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize embedding manager.

        Args:
            config: Embedding configuration (uses defaults if None)
        """
        self.config = config or EmbeddingConfig()
        self._model = None
        self._cache: Dict[str, np.ndarray] = {}
        self._anchor_embeddings: Dict[str, np.ndarray] = {}
        self._specificity_centroids: Dict[str, Dict[str, np.ndarray]] = {}

    @property
    def model(self):
        """Lazy load the model on first use"""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            print(f"[INFO] Loading embedding model: {self.config.model_name}")
            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device
            )
            print(f"[OK] Embedding model loaded successfully")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            )

    def encode(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Encode a single text to embedding vector.

        Args:
            text: Input text to encode
            use_cache: Whether to use/update cache

        Returns:
            Normalized embedding vector (384 dimensions for MiniLM)
        """
        if use_cache and text in self._cache:
            return self._cache[text]

        embedding = self.model.encode(
            text,
            normalize_embeddings=self.config.normalize,
            show_progress_bar=False
        )

        if use_cache:
            self._cache[text] = embedding

        return embedding

    def encode_batch(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """
        Batch encode multiple texts efficiently.

        Args:
            texts: List of texts to encode
            use_cache: Whether to use/update cache

        Returns:
            Array of embedding vectors (N x 384)
        """
        if not texts:
            return np.array([])

        # Check cache for existing embeddings
        if use_cache:
            cached = []
            to_encode = []
            to_encode_indices = []

            for i, text in enumerate(texts):
                if text in self._cache:
                    cached.append((i, self._cache[text]))
                else:
                    to_encode.append(text)
                    to_encode_indices.append(i)

            # Encode only new texts
            if to_encode:
                new_embeddings = self.model.encode(
                    to_encode,
                    normalize_embeddings=self.config.normalize,
                    show_progress_bar=False
                )

                # Update cache
                for text, emb in zip(to_encode, new_embeddings):
                    self._cache[text] = emb

            # Combine cached and new embeddings in original order
            result = np.zeros((len(texts), self.embedding_dim))
            for i, emb in cached:
                result[i] = emb
            for i, idx in enumerate(to_encode_indices):
                result[idx] = new_embeddings[i]

            return result
        else:
            return self.model.encode(
                texts,
                normalize_embeddings=self.config.normalize,
                show_progress_bar=False
            )

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()

    def precompute_anchors(self, parameter_anchors: Dict[str, List[str]]):
        """
        Pre-compute anchor embeddings for parameter detection.

        Args:
            parameter_anchors: Dict mapping parameter names to anchor phrases
        """
        print("[INFO] Pre-computing anchor embeddings...")
        for param_name, anchors in parameter_anchors.items():
            embeddings = self.encode_batch(anchors)
            self._anchor_embeddings[param_name] = embeddings
        print(f"[OK] Pre-computed anchors for {len(parameter_anchors)} parameters")

    def get_anchor_embeddings(self, param_name: str) -> Optional[np.ndarray]:
        """Get pre-computed anchor embeddings for a parameter"""
        return self._anchor_embeddings.get(param_name)

    def precompute_specificity_centroids(
        self,
        specificity_data: Dict[str, Dict[str, List[str]]]
    ):
        """
        Pre-compute centroids for specificity levels.

        Args:
            specificity_data: Dict[param_type][level] = list of examples
                e.g., {"date": {"specific": [...], "moderate": [...], "vague": [...]}}
        """
        print("[INFO] Pre-computing specificity centroids...")
        for param_type, levels in specificity_data.items():
            self._specificity_centroids[param_type] = {}
            for level, examples in levels.items():
                embeddings = self.encode_batch(examples)
                centroid = np.mean(embeddings, axis=0)
                self._specificity_centroids[param_type][level] = centroid
        print(f"[OK] Pre-computed centroids for {len(specificity_data)} parameter types")

    def get_specificity_centroids(self, param_type: str) -> Optional[Dict[str, np.ndarray]]:
        """Get pre-computed specificity centroids for a parameter type"""
        return self._specificity_centroids.get(param_type)

    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity (-1 to 1, higher = more similar)
        """
        # If already normalized, dot product = cosine similarity
        if self.config.normalize:
            return float(np.dot(embedding1, embedding2))
        else:
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def cosine_similarity_batch(
        self,
        query: np.ndarray,
        candidates: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and multiple candidates.

        Args:
            query: Query embedding (1D array)
            candidates: Candidate embeddings (2D array, N x dim)

        Returns:
            Array of similarities (N,)
        """
        if self.config.normalize:
            return np.dot(candidates, query)
        else:
            query_norm = np.linalg.norm(query)
            candidate_norms = np.linalg.norm(candidates, axis=1)

            # Avoid division by zero
            valid = (query_norm > 0) & (candidate_norms > 0)
            similarities = np.zeros(len(candidates))
            similarities[valid] = np.dot(candidates[valid], query) / (
                query_norm * candidate_norms[valid]
            )
            return similarities

    def clear_cache(self):
        """Clear the embedding cache"""
        self._cache.clear()

    def save_precomputed(self, filepath: str):
        """
        Save pre-computed embeddings to file.

        Args:
            filepath: Path to save file
        """
        data = {
            "anchor_embeddings": self._anchor_embeddings,
            "specificity_centroids": self._specificity_centroids
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"[OK] Saved pre-computed embeddings to {filepath}")

    def load_precomputed(self, filepath: str) -> bool:
        """
        Load pre-computed embeddings from file.

        Args:
            filepath: Path to load file

        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            self._anchor_embeddings = data.get("anchor_embeddings", {})
            self._specificity_centroids = data.get("specificity_centroids", {})
            print(f"[OK] Loaded pre-computed embeddings from {filepath}")
            return True
        except Exception as e:
            print(f"[WARN] Failed to load pre-computed embeddings: {e}")
            return False


def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax values"""
    exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
    return exp_x / exp_x.sum()
