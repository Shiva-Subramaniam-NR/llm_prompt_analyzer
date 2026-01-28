# Prompt Quality Analysis Framework

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive semantic analysis framework for evaluating LLM prompt quality. Designed for **developers building LLM applications** to ensure their system prompts and user prompts are well-aligned, consistent, and effective.

**Authors:** Research Partnership - Shiva & Claude

---

## 🎯 What is This?

This framework helps developers analyze and improve the quality of prompts used in LLM applications by detecting:

- ❌ **Missing Required Parameters** - User didn't provide info the system needs
- 🔴 **Contradictions** - Internal conflicts within prompts
- 📏 **Verbosity Issues** - Overly long prompts with buried critical directives
- 🔀 **Misalignments** - User prompts that violate system constraints
- ⚠️ **Constraint Violations** - User requests that break MUST/NEVER rules

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/prompt-quality-analyzer.git
cd prompt-quality-analyzer

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Basic Usage

```python
from v2.prompt_quality_analyzer import PromptQualityAnalyzer

analyzer = PromptQualityAnalyzer()

system_prompt = """
You are a flight booking assistant.
REQUIRED: origin, destination, date
MUST: Verify all booking details
NEVER: Share payment information
"""

user_prompt = "Book a flight from New York to London on Dec 25th"

# Optional: Provide artifacts (files referenced in prompts)
artifacts = {
    'booking_policy': 'docs/policy.pdf',
    'terms': 'docs/terms.txt'
}

report = analyzer.analyze(system_prompt, user_prompt, artifacts=artifacts)

print(f"Overall Score: {report.overall_score:.1f}/10")
print(f"Quality: {report.quality_rating.value}")
print(f"Can Fulfill Request: {report.is_fulfillable}")
```

## 📊 Key Features

- 🧠 **Semantic Understanding** - Uses sentence-transformers, not regex
- 📈 **Comprehensive Scoring** - Overall quality (0-10) with component breakdown
- 🔍 **5 Core Components** - Parser, Alignment, Contradiction, Verbosity, Orchestrator
- 📦 **Production-Ready** - JSON export, confidence scores, recommendations
- ⚡ **Fast** - ~300-800ms per analysis, no LLM calls needed
- 📎 **Artifact Support** - Upload PDFs, images, documents referenced in prompts (Phase 1)

## 🧪 Running Tests

```bash
python test_prompt_quality_analyzer.py    # Full demo
python test_alignment_checker.py          # Alignment tests
python test_contradiction_detector.py     # Contradiction tests
```

## 📈 Performance

- Initialization: ~3-5 seconds
- Analysis: ~300-800ms per prompt pair
- Memory: ~400MB
- Accuracy: 50-85% depending on component

## 📄 License

MIT License

---

**Built for developers, by developers. Make your LLM prompts bulletproof! 🚀**
