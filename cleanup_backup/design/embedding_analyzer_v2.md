# Prompt Analysis Framework v2.0 - Technical Design
## Embedding-Based Semantic Analysis

**Authors:** Shiva & Claude
**Status:** Design Phase
**Date:** January 2025

---

## 1. Problem Statement

The current regex-based approach (v1.0) suffers from:
- **Brittleness**: Exact pattern matching fails on variations
- **Maintenance burden**: New patterns needed for each edge case
- **False positives/negatives**: "to fly" matches before "to Hyderabad"
- **No semantic understanding**: Can't handle paraphrasing or synonyms

**Goal:** Replace rigid pattern matching with semantic similarity using embeddings.

---

## 2. Core Concepts

### 2.1 Semantic Parameter Detection

Instead of regex patterns, we define **anchor embeddings** for each parameter:

```
PARAMETER_ANCHORS = {
    "origin": [
        "departure city",
        "flying from",
        "starting point",
        "source location"
    ],
    "destination": [
        "arrival city",
        "going to",
        "target location",
        "ending point"
    ],
    ...
}
```

For each noun/entity in the prompt, compute cosine similarity to all anchors:

```
similarity(embed("Chennai"), embed("departure city")) = 0.31
similarity(embed("Chennai"), embed("arrival city")) = 0.29

# But with context:
similarity(embed("from Chennai"), embed("departure city")) = 0.84
```

### 2.2 Vagueness as Information Entropy

**Key Insight:** Vague words map to larger regions in semantic space.

```
                    Embedding Space

    "January 15"  →      •           (tight, specific)

    "next week"   →    • • •         (spread across 7 days)
                       • • • •

    "soon"        →  • • • • • •     (diffuse, unbounded)
                     • • • • • •
                     • • • • • •
```

**Metrics:**
1. **Semantic Spread (σ)**: Standard deviation of distances to nearest temporal/quantity anchors
2. **Specificity Score**: `1 / (1 + σ)`
3. **Information Content**: `-log(P(word|context))` using language model

### 2.3 Mathematical Framework

#### Vagueness Score Formula

```
V(prompt) = α × Completeness_Score + β × Specificity_Score + γ × Ambiguity_Score

Where:
- Completeness = Σ max_similarity(param_anchor, prompt_entities) for all params
- Specificity = 1 - mean(semantic_spread(extracted_values))
- Ambiguity = count(polysemous_terms) / total_terms
```

#### Parameter Detection

```python
def detect_parameter(entity: str, context: str, anchors: List[str]) -> Tuple[str, float]:
    """
    Returns (parameter_name, confidence_score)

    Uses contextual embedding: embed(context_window around entity)
    """
    entity_embedding = model.encode(f"{context_left} {entity} {context_right}")

    scores = {}
    for param_name, param_anchors in PARAMETER_ANCHORS.items():
        anchor_embeddings = model.encode(param_anchors)
        max_sim = max(cosine_similarity(entity_embedding, a) for a in anchor_embeddings)
        scores[param_name] = max_sim

    best_param = max(scores, key=scores.get)
    return (best_param, scores[best_param])
```

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROMPT INPUT                                │
│  "Book flight from Chennai to Mumbai on 15th Jan, morning"      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Tokenize   │→ │  NER Extract │→ │ Chunk Context│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  Output: [("Chennai", "GPE"), ("Mumbai", "GPE"), ...]           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDING LAYER                               │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Sentence Transformer (all-MiniLM-L6-v2)             │       │
│  │  - Entity embeddings (with context window)            │       │
│  │  - Full prompt embedding                              │       │
│  └──────────────────────────────────────────────────────┘       │
│  Output: {entity: vector_384d, ...}                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SEMANTIC ANALYSIS LAYER                          │
│  ┌────────────────────┐  ┌────────────────────┐                 │
│  │ Parameter Matcher  │  │ Vagueness Analyzer │                 │
│  │                    │  │                    │                 │
│  │ - Anchor similarity│  │ - Semantic spread  │                 │
│  │ - Context scoring  │  │ - Entropy calc     │                 │
│  │ - Confidence thresh│  │ - Specificity map  │                 │
│  └────────────────────┘  └────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
│  {                                                               │
│    "parameters": {                                               │
│      "origin": {"value": "Chennai", "confidence": 0.89},        │
│      "destination": {"value": "Mumbai", "confidence": 0.91},    │
│      "date": {"value": "15th Jan", "confidence": 0.85}          │
│    },                                                            │
│    "vagueness_score": 2.3,                                       │
│    "specificity_breakdown": {...}                                │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Component Design

### 4.1 Domain Configuration (v2)

```python
@dataclass
class DomainConfigV2:
    """Embedding-based domain configuration"""

    name: str

    # Anchor phrases for each parameter (used for embedding similarity)
    parameter_anchors: Dict[str, List[str]]

    # Specificity reference points (for measuring vagueness)
    specificity_anchors: Dict[str, Dict[str, List[str]]]

    # Threshold for parameter detection confidence
    confidence_threshold: float = 0.65

    # Weights for vagueness calculation
    weights: Dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.5,
        "specificity": 0.3,
        "ambiguity": 0.2
    })


# Example for Flight Booking
FLIGHT_BOOKING_V2 = DomainConfigV2(
    name="flight_booking",

    parameter_anchors={
        "origin": [
            "departure city",
            "leaving from",
            "flying from",
            "starting from",
            "departing from",
            "source airport"
        ],
        "destination": [
            "arrival city",
            "going to",
            "flying to",
            "landing at",
            "destination airport",
            "reaching"
        ],
        "date": [
            "travel date",
            "departure date",
            "on which day",
            "date of journey",
            "when to fly"
        ],
        "time_preference": [
            "departure time",
            "flight timing",
            "preferred time",
            "time of day",
            "when during the day"
        ],
        "class": [
            "cabin class",
            "seat class",
            "travel class",
            "economy or business",
            "seating preference"
        ],
        "budget": [
            "maximum price",
            "cost limit",
            "budget constraint",
            "price range",
            "how much to spend"
        ]
    },

    specificity_anchors={
        "date": {
            "specific": ["January 15 2025", "March 20", "December 3rd"],
            "moderate": ["next Monday", "this Friday", "coming weekend"],
            "vague": ["soon", "sometime", "in a few days", "later"]
        },
        "time": {
            "specific": ["9:30 AM", "14:00", "6 PM sharp"],
            "moderate": ["morning", "afternoon", "evening"],
            "vague": ["early", "late", "sometime during the day"]
        },
        "budget": {
            "specific": ["8000 rupees", "$500", "exactly 10k"],
            "moderate": ["under 10000", "around 5k", "less than 15000"],
            "vague": ["cheap", "affordable", "not too expensive", "reasonable"]
        }
    },

    confidence_threshold=0.65
)
```

### 4.2 Embedding Manager

```python
class EmbeddingManager:
    """Manages embedding model and caching"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self._cache: Dict[str, np.ndarray] = {}
        self._anchor_embeddings: Dict[str, np.ndarray] = {}

    def encode(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Encode text to embedding vector"""
        if use_cache and text in self._cache:
            return self._cache[text]

        embedding = self.model.encode(text, normalize_embeddings=True)

        if use_cache:
            self._cache[text] = embedding

        return embedding

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Batch encode for efficiency"""
        return self.model.encode(texts, normalize_embeddings=True)

    def precompute_anchors(self, domain_config: DomainConfigV2):
        """Pre-compute anchor embeddings for fast lookup"""
        for param, anchors in domain_config.parameter_anchors.items():
            embeddings = self.encode_batch(anchors)
            self._anchor_embeddings[param] = embeddings

    def get_anchor_embeddings(self, param: str) -> np.ndarray:
        """Get pre-computed anchor embeddings"""
        return self._anchor_embeddings.get(param)
```

### 4.3 Semantic Parameter Detector

```python
class SemanticParameterDetector:
    """Detect parameters using embedding similarity"""

    def __init__(self, embedding_manager: EmbeddingManager, domain: DomainConfigV2):
        self.embeddings = embedding_manager
        self.domain = domain
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities_with_context(self, prompt: str) -> List[EntityContext]:
        """Extract entities with surrounding context window"""
        doc = self.nlp(prompt)
        entities = []

        for ent in doc.ents:
            # Get context window (5 tokens before and after)
            start = max(0, ent.start - 5)
            end = min(len(doc), ent.end + 5)
            context = doc[start:end].text

            entities.append(EntityContext(
                text=ent.text,
                label=ent.label_,
                context=context,
                start=ent.start_char,
                end=ent.end_char
            ))

        # Also extract noun chunks not caught by NER
        for chunk in doc.noun_chunks:
            if not any(e.text == chunk.text for e in entities):
                start = max(0, chunk.start - 5)
                end = min(len(doc), chunk.end + 5)
                context = doc[start:end].text

                entities.append(EntityContext(
                    text=chunk.text,
                    label="NOUN_CHUNK",
                    context=context,
                    start=chunk.start_char,
                    end=chunk.end_char
                ))

        return entities

    def match_to_parameters(self, entities: List[EntityContext]) -> Dict[str, ParameterMatch]:
        """Match entities to domain parameters using semantic similarity"""
        results = {}

        for entity in entities:
            # Encode entity WITH context for better semantic understanding
            entity_embedding = self.embeddings.encode(entity.context)

            best_param = None
            best_score = 0.0

            for param_name in self.domain.parameter_anchors:
                anchor_embeddings = self.embeddings.get_anchor_embeddings(param_name)

                # Compute max similarity to any anchor
                similarities = cosine_similarity(
                    entity_embedding.reshape(1, -1),
                    anchor_embeddings
                )[0]

                max_sim = np.max(similarities)

                if max_sim > best_score and max_sim > self.domain.confidence_threshold:
                    best_score = max_sim
                    best_param = param_name

            if best_param:
                # Only keep if better than existing match for this param
                if best_param not in results or results[best_param].confidence < best_score:
                    results[best_param] = ParameterMatch(
                        parameter=best_param,
                        value=entity.text,
                        confidence=best_score,
                        context=entity.context
                    )

        return results
```

### 4.4 Vagueness Analyzer (Embedding-Based)

```python
class SemanticVaguenessAnalyzer:
    """Calculate vagueness using semantic spread in embedding space"""

    def __init__(self, embedding_manager: EmbeddingManager, domain: DomainConfigV2):
        self.embeddings = embedding_manager
        self.domain = domain
        self._precompute_specificity_centroids()

    def _precompute_specificity_centroids(self):
        """Compute centroids for specific/moderate/vague anchors"""
        self.specificity_centroids = {}

        for param, levels in self.domain.specificity_anchors.items():
            self.specificity_centroids[param] = {}
            for level, examples in levels.items():
                embeddings = self.embeddings.encode_batch(examples)
                centroid = np.mean(embeddings, axis=0)
                self.specificity_centroids[param][level] = centroid

    def calculate_specificity(self, value: str, param_type: str) -> float:
        """
        Calculate specificity score (0-1) based on distance to specificity centroids

        Returns:
            1.0 = very specific
            0.5 = moderate
            0.0 = very vague
        """
        if param_type not in self.specificity_centroids:
            return 0.5  # Unknown parameter type

        value_embedding = self.embeddings.encode(value)
        centroids = self.specificity_centroids[param_type]

        # Calculate distances to each specificity level
        distances = {}
        for level, centroid in centroids.items():
            distances[level] = cosine_similarity(
                value_embedding.reshape(1, -1),
                centroid.reshape(1, -1)
            )[0][0]

        # Weighted score: closer to "specific" = higher score
        # Using softmax-like weighting
        specific_weight = distances.get("specific", 0)
        moderate_weight = distances.get("moderate", 0)
        vague_weight = distances.get("vague", 0)

        total = specific_weight + moderate_weight + vague_weight
        if total == 0:
            return 0.5

        specificity = (specific_weight * 1.0 + moderate_weight * 0.5 + vague_weight * 0.0) / total
        return specificity

    def calculate_semantic_spread(self, value: str) -> float:
        """
        Calculate how "spread out" a term is in semantic space

        Vague terms like "soon" have high spread (could mean many things)
        Specific terms like "January 15" have low spread
        """
        # Generate variations/interpretations
        variations = self._generate_interpretations(value)

        if len(variations) <= 1:
            return 0.0  # No spread

        # Encode all variations
        embeddings = self.embeddings.encode_batch(variations)

        # Calculate centroid
        centroid = np.mean(embeddings, axis=0)

        # Calculate standard deviation of distances to centroid
        distances = [np.linalg.norm(e - centroid) for e in embeddings]
        spread = np.std(distances)

        return spread

    def _generate_interpretations(self, value: str) -> List[str]:
        """Generate possible interpretations of a value"""
        value_lower = value.lower()

        # Temporal interpretations
        if value_lower in ["soon", "later", "sometime"]:
            return ["tomorrow", "next week", "next month", "in a few days", "in an hour"]
        elif value_lower in ["morning", "early morning"]:
            return ["6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM"]
        elif value_lower == "next week":
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        elif value_lower in ["cheap", "affordable", "reasonable"]:
            return ["1000 rupees", "3000 rupees", "5000 rupees", "8000 rupees", "10000 rupees"]

        # Specific value - no spread
        return [value]

    def analyze(self, detected_params: Dict[str, ParameterMatch],
                prompt: str) -> VaguenessResult:
        """Complete vagueness analysis"""

        total_params = len(self.domain.parameter_anchors)
        detected_count = len(detected_params)

        # 1. Completeness score (0-10, 10 = all missing)
        missing_ratio = 1 - (detected_count / total_params)
        completeness_score = 10 * (missing_ratio ** 0.7)  # Exponential penalty

        # 2. Specificity score (0-10, 10 = all vague)
        specificity_scores = []
        for param_name, match in detected_params.items():
            # Map parameter to specificity category
            if param_name in ["date"]:
                spec = self.calculate_specificity(match.value, "date")
            elif param_name in ["time_preference"]:
                spec = self.calculate_specificity(match.value, "time")
            elif param_name in ["budget"]:
                spec = self.calculate_specificity(match.value, "budget")
            else:
                spec = 0.8  # Assume locations/classes are reasonably specific

            specificity_scores.append(spec)

        avg_specificity = np.mean(specificity_scores) if specificity_scores else 0.5
        specificity_score = 10 * (1 - avg_specificity)

        # 3. Combined vagueness score
        weights = self.domain.weights
        vagueness_score = (
            weights["completeness"] * completeness_score +
            weights["specificity"] * specificity_score
        )

        # Apply critical parameter penalty
        missing_params = set(self.domain.parameter_anchors.keys()) - set(detected_params.keys())
        if "origin" in missing_params and "destination" in missing_params:
            vagueness_score = min(10, vagueness_score + 2.0)
        elif "origin" in missing_params or "destination" in missing_params:
            vagueness_score = min(10, vagueness_score + 1.0)

        return VaguenessResult(
            score=round(vagueness_score, 1),
            interpretation=self._interpret(vagueness_score),
            completeness_score=round(completeness_score, 1),
            specificity_score=round(specificity_score, 1),
            missing_params=list(missing_params),
            param_specificity={p: s for p, s in zip(detected_params.keys(), specificity_scores)}
        )

    def _interpret(self, score: float) -> str:
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
```

---

## 5. Data Structures

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np


@dataclass
class EntityContext:
    """Entity with surrounding context"""
    text: str
    label: str
    context: str
    start: int
    end: int


@dataclass
class ParameterMatch:
    """Matched parameter with confidence"""
    parameter: str
    value: str
    confidence: float
    context: str


@dataclass
class VaguenessResult:
    """Complete vagueness analysis result"""
    score: float
    interpretation: str
    completeness_score: float
    specificity_score: float
    missing_params: List[str]
    param_specificity: Dict[str, float]


@dataclass
class AnalysisResult:
    """Complete prompt analysis result"""
    prompt: str
    detected_parameters: Dict[str, ParameterMatch]
    vagueness: VaguenessResult
    high_weightage_words: List[Dict]  # Backward compatibility
```

---

## 6. API Design

```python
class PromptAnalyzerV2:
    """Main analyzer using embedding-based approach"""

    def __init__(self, domain: str = "flight_booking",
                 model: str = "all-MiniLM-L6-v2"):
        self.embedding_manager = EmbeddingManager(model)
        self.domain = self._load_domain(domain)

        # Pre-compute anchor embeddings
        self.embedding_manager.precompute_anchors(self.domain)

        self.param_detector = SemanticParameterDetector(
            self.embedding_manager, self.domain
        )
        self.vagueness_analyzer = SemanticVaguenessAnalyzer(
            self.embedding_manager, self.domain
        )

    def analyze(self, prompt: str) -> AnalysisResult:
        """Analyze a prompt and return complete results"""

        # 1. Extract entities with context
        entities = self.param_detector.extract_entities_with_context(prompt)

        # 2. Match to parameters using semantic similarity
        detected_params = self.param_detector.match_to_parameters(entities)

        # 3. Analyze vagueness
        vagueness = self.vagueness_analyzer.analyze(detected_params, prompt)

        # 4. Extract high-weightage words (for backward compatibility)
        high_weightage = self._extract_high_weightage(detected_params)

        return AnalysisResult(
            prompt=prompt,
            detected_parameters=detected_params,
            vagueness=vagueness,
            high_weightage_words=high_weightage
        )
```

---

## 7. Advantages Over v1.0

| Aspect | v1.0 (Regex) | v2.0 (Embeddings) |
|--------|--------------|-------------------|
| Pattern matching | Exact, brittle | Semantic, flexible |
| New variations | Requires new regex | Automatic generalization |
| Synonym handling | Manual lists | Built into embeddings |
| Vagueness detection | Word lists | Mathematical (entropy/spread) |
| Cross-language | English only | Multilingual models available |
| Confidence scores | Binary (match/no-match) | Continuous (0.0-1.0) |
| Maintenance | High (pattern updates) | Low (model handles variations) |

---

## 8. Dependencies

```
sentence-transformers>=2.2.0
numpy>=1.21.0
spacy>=3.0.0
scikit-learn>=1.0.0  # for cosine_similarity
```

---

## 9. Performance Considerations

1. **Model Loading**: ~2-3 seconds cold start (cache model in memory)
2. **Inference**: ~10-50ms per prompt (batch for throughput)
3. **Memory**: ~100MB for all-MiniLM-L6-v2
4. **Caching**: Pre-compute anchor embeddings, cache prompt embeddings

---

## 10. Future Enhancements

1. **Fine-tuned embeddings**: Train on domain-specific data
2. **LLM-based interpretation**: Use Claude/GPT for nuanced vagueness analysis
3. **Multi-domain support**: Plug-and-play domain configs
4. **Active learning**: Improve from user feedback on detection accuracy

---

## 11. Design Decisions (Finalized)

### Decision 1: Embedding Model
**Choice:** `all-MiniLM-L6-v2` (80MB)
- Fast inference (~10ms/prompt)
- Sufficient for constrained flight booking vocabulary
- Can upgrade to MPNet later if accuracy insufficient

### Decision 2: Compound Parameters
**Choice:** Flatten to separate parameters
```python
MANDATORY_PARAMS = {
    "origin": ...,
    "destination": ...,
    "date_outbound": ...,      # For one-way or outbound leg
    "date_return": ...,        # Optional, for round trips
    "time_preference": ...,
    "class": ...,
    "budget": ...
}
```

### Decision 3: Specificity Anchors
**Choice:** Learn from synthetic data
- Generate labeled examples programmatically
- Cluster embeddings to find natural boundaries
- No external data dependency

**Synthetic Data Generation Strategy:**
```python
SYNTHETIC_DATA = {
    "date": {
        "specific": generate_exact_dates(n=100),      # "January 15 2025", "March 3rd"
        "moderate": generate_relative_dates(n=100),   # "next Monday", "this Friday"
        "vague": ["soon", "later", "sometime", "in a few days", ...] * 20
    },
    "time": {
        "specific": generate_exact_times(n=100),      # "9:30 AM", "14:00", "6 PM"
        "moderate": ["morning", "afternoon", "evening", "night"] * 25,
        "vague": ["early", "late", "around noon", "sometime"] * 25
    },
    "budget": {
        "specific": generate_exact_amounts(n=100),    # "8000 rupees", "₹5000"
        "moderate": generate_range_amounts(n=100),    # "under 10k", "5000-8000"
        "vague": ["cheap", "affordable", "reasonable", "not expensive"] * 25
    }
}
```

### Decision 4: Follow-up Question Generation
**Choice:** Hybrid (Templates + LLM)
- **Default:** Template-based questions (fast, free)
- **LLM trigger:** When `vagueness_score > 7.0`
- LLM generates context-aware, conversational follow-ups

```python
class FollowUpGenerator:
    def generate(self, analysis_result, use_llm_threshold=7.0):
        if analysis_result.vagueness.score > use_llm_threshold:
            return self._llm_generate(analysis_result)
        else:
            return self._template_generate(analysis_result)
```

---

## 12. Final Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         PROMPT INPUT                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  EMBEDDING LAYER: all-MiniLM-L6-v2 (80MB, ~10ms)               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  PARAMETER DETECTION: Cosine similarity to anchor embeddings   │
│  - Confidence threshold: 0.65                                   │
│  - Flattened params (date_outbound, date_return separate)      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  VAGUENESS ANALYSIS: Learned specificity clusters              │
│  - Synthetic data → K-means clustering                         │
│  - Specificity = distance to specific/moderate/vague centroids │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  FOLLOW-UP GENERATION: Hybrid                                   │
│  - vagueness ≤ 7.0 → Template questions                        │
│  - vagueness > 7.0 → LLM-generated questions                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. Implementation Plan

| Phase | Task | Effort |
|-------|------|--------|
| **Phase 1** | EmbeddingManager + synthetic data generation | Core |
| **Phase 2** | SemanticParameterDetector with anchor matching | Core |
| **Phase 3** | Specificity cluster training | Core |
| **Phase 4** | SemanticVaguenessAnalyzer | Core |
| **Phase 5** | Hybrid follow-up generator | Enhancement |
| **Phase 6** | Test suite + benchmark vs v1.0 | Validation |
| **Phase 7** | Performance optimization + caching | Polish |

---

## 14. Success Metrics

1. **Accuracy:** ≥95% parameter detection on test suite (vs v1.0 baseline)
2. **No false positives:** "need to travel" should NOT detect origin
3. **Vagueness calibration:** Test 4 ("I need to travel soon") scores ≥8.0
4. **Latency:** <100ms per prompt (including embedding)
5. **Specificity discrimination:** "Jan 15" vs "soon" should differ by ≥0.7
