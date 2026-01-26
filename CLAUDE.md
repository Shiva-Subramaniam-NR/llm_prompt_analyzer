# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Prompt Analysis Framework for analyzing LLM prompts to extract high-weightage words and measure vagueness. The project has two major versions:

- **v1 (root level)**: Regex/pattern-based analysis using spaCy NER
- **v2 (`v2/` directory)**: Embedding-based semantic analysis using sentence-transformers

Currently focused on the **flight booking domain**, with architecture designed for future domain expansion.

## Commands

### Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run the Framework
```bash
# Interactive mode (v1)
python main.py

# Run v2 tests with embedding-based analysis
python test_v2_embedding.py

# Compare v1 vs v2 results
python test_v2_embedding.py --compare

# Test v2 weightage extraction only
python test_v2.py
```

## Architecture

### Two-Version System

The codebase maintains two parallel implementations:

**v1 (Root Level)** - Regex + spaCy NER:
- `weightage.py` - `WeightageExtractorV2`: Extracts high-weightage words using spaCy NER, pattern matching, and POS tagging
- `vagueness.py` - `VaguenessCalculator`: Calculates vagueness using regex parameter detection with exponential penalty for missing params
- `prompt_analyzer.py` - `PromptAnalyzer`: Orchestrates v1 analysis pipeline
- `config/domain_config.py` - `FlightBookingDomain`: Regex patterns for mandatory parameters

**v2 (`v2/` Directory)** - Embedding-based Semantic Analysis:
- `embedding_manager.py` - `EmbeddingManager`: Manages sentence-transformers model, caching, and similarity computations
- `parameter_detector.py` - `SemanticParameterDetector`: Detects parameters using semantic similarity to anchor embeddings
- `vagueness_analyzer.py` - `SemanticVaguenessAnalyzer`: Measures vagueness using specificity centroids from synthetic data
- `analyzer.py` - `PromptAnalyzerV2`: Main orchestrator for v2 pipeline
- `domain_config_v2.py` - `DomainConfigV2`: Semantic anchor phrases instead of regex patterns
- `synthetic_data.py` - Generates labeled training data for specificity clustering

### Key Concepts

**Weightage Scoring** (v1):
- Final weightage = 0.4 × specificity + 0.4 × constraint_power + 0.2 × (1 - replaceability)
- High weightage threshold: >= 0.6

**Vagueness Scoring** (both versions):
- Uses exponential penalty: `10 × (missing_ratio)^0.7`
- Combines completeness (50%) + specificity (35%) + ambiguity (15%)
- Critical parameter penalties: +2.0 for both origin+destination missing, +1.0 for either, +0.5 for date
- Score interpretation: 0-1.5 (very specific) → 7.5+ (extremely vague)

**v2 Parameter Detection Flow**:
1. Extract entities with spaCy NER + noun chunks
2. Embed entities with surrounding context
3. Compare to pre-computed parameter anchor embeddings
4. Use context patterns as confirmation/fallback for locations

### Domain Configuration

To add a new domain:
- v1: Create a class with `MANDATORY_PARAMS` (regex patterns), `VAGUE_TERMS`, and `CONSTRAINT_KEYWORDS` in `config/`
- v2: Create a `DomainConfigV2` with `parameter_anchors` (semantic phrases), `entity_type_mapping`, and `param_specificity_type` in `v2/domain_config_v2.py`

## Testing

Run unit tests for v1:
```bash
python main.py  # Select option 1 for test suite
```

Results are saved to `outputs/prompt_analysis_results.json` (v1) and `outputs/v2_test_results.json` (v2).
