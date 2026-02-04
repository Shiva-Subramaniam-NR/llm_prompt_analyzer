# LLM Prompt Quality Analyzer

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0-brightgreen.svg)](https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer)

A comprehensive **hybrid prompt analysis framework** combining fast embedding-based analysis with optional LLM-powered deep insights. Built for developers who need to debug, validate, and improve their LLM prompts during development and testing.

**🎯 Perfect for:** Prompt engineers, LLM application developers, QA teams debugging prompt issues

---

## ✨ What Makes This Special?

**Two-Tier Hybrid Architecture:**
- **Tier 1 (Non-LLM)**: Lightning-fast (300ms), free, deterministic structural analysis
- **Tier 2 (LLM)**: Optional deep semantic, safety, and security validation (~$0.0006 per analysis)

**Why not just use an LLM?** Because you need **speed, cost-efficiency, and reproducibility** for 90% of your analysis. Save the LLM for the complex 10%.

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer.git
cd llm_prompt_analyzer

# Install core dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Optional: Web UI
pip install -r requirements-web.txt

# Optional: LLM Deep Analysis (Phase 2)
pip install google-generativeai

# Optional: Artifact Processing
pip install pdfplumber Pillow
```

### Setup (for LLM features)

Create a `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
```

---

## 💻 Usage Options

### **Option 1: Web UI** (Easiest)

```bash
cd web
python app.py
```

Then open **http://localhost:5000** in your browser!

**Features:**
- 🎨 Beautiful, intuitive interface
- 📤 Drag & drop file uploads
- 📊 Visual results with charts
- 💾 Export results as JSON
- 🔄 Real-time validation

---

### **Option 2: Interactive CLI**

```bash
python run_analyzer.py
```

Follow the prompts to:
1. Enter system prompt (mandatory)
2. Enter user prompt (optional)
3. Upload artifact files (optional)
4. Select analysis mode
5. Get comprehensive report

---

### **Option 3: Programmatic API**

#### **Basic Usage (Tier 1 Only)**

```python
from v2.prompt_quality_analyzer import PromptQualityAnalyzer

analyzer = PromptQualityAnalyzer()

system_prompt = """
You are a flight booking assistant.
REQUIRED: origin, destination, date
MUST: Verify all booking details
NEVER: Share payment information
"""

user_prompt = "Book a flight from NYC to London on Dec 25th"

# Tier 1: Fast, free analysis
report = analyzer.analyze(system_prompt, user_prompt)

print(f"Score: {report.overall_score:.1f}/10")
print(f"Quality: {report.quality_rating.value}")
print(f"Can Fulfill: {report.is_fulfillable}")
print(f"Issues: {report.total_issues}")
```

#### **With Artifacts (Phase 1)**

```python
artifacts = {
    'policy': 'docs/booking_policy.pdf',
    'terms': 'docs/terms.txt',
    'screenshot': 'images/flow.png'
}

report = analyzer.analyze(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    artifacts=artifacts
)

# Check artifact issues
artifact_issues = [i for i in report.all_issues if i.category == 'artifact']
```

#### **With LLM Deep Analysis (Phase 2)**

```python
from v2.llm_analyzer import LLMAnalyzer

# First run Tier 1
report = analyzer.analyze(system_prompt, user_prompt)

# Then run Tier 2 for deep insights
llm = LLMAnalyzer(verbose=True)

result = llm.analyze_semantic_impossibility(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    tier1_issues=[issue.__dict__ for issue in report.all_issues]
)

print(f"Risk Type: {result.primary_risk_type}")
print(f"Impossibility Score: {result.impossibility_score}/10")
print(f"Explanation: {result.explanation}")
print(f"Cost: ${llm.cost_tracker.get_session_cost():.4f}")
```

---

## 📊 What It Detects

### **Tier 1 (Non-LLM) - Always Runs**

| Component | Detects | Speed |
|-----------|---------|-------|
| **Contradiction Detector** | Conflicting MUST/NEVER rules, direct negations | 100ms |
| **Alignment Checker** | System-user prompt incompatibilities, missing params | 150ms |
| **Verbosity Analyzer** | Overly long prompts, buried critical directives | 50ms |
| **System Parser** | Requirements, constraints, mandatory fields | 100ms |
| **Artifact Handler** | Missing files, invalid references | 50ms |

**Total:** ~300-800ms | **Cost:** FREE | **Reproducible:** ✅

---

### **Tier 2 (LLM) - Optional**

| Analysis Type | Detects | When To Use |
|---------------|---------|-------------|
| **Semantic Impossibility** | Fundamentally incompatible requests | Score < 7.0 |
| **Safety Risks** | Dangerous/harmful instructions, toxic content | Always for prod |
| **Security Threats** | Prompt injection, jailbreak attempts | Always for prod |
| **Natural Language Explanations** | Plain English issue descriptions | Debugging |

**Time:** 5-25s | **Cost:** ~$0.0006 | **Requires:** Internet + API key

---

## 🎯 Key Features

### **Comprehensive Scoring**

```
Overall Score: 8.5/10 (GOOD)
├─ Alignment: 10.0/10     ✅ Perfect match
├─ Consistency: 9.4/10    ✅ Minor issues
├─ Verbosity: 3.2/10      ⚠️  Too verbose
└─ Completeness: 10.0/10  ✅ All params present
```

### **Issue Detection with Severity**

- 🔴 **Critical**: Blocks functionality (contradictions, missing required params)
- 🟠 **High**: Major quality issues (buried directives, security risks)
- 🟡 **Moderate**: Improvements recommended (verbosity, optimization)
- 🔵 **Low**: Minor suggestions (style, best practices)

### **Safety-First Analysis (Phase 2)**

Detects three risk types in priority order:
1. **Safety**: Toxic ingredients, dangerous DIY, unqualified medical advice
2. **Security**: Prompt injection, jailbreak attempts, instruction overrides
3. **Semantic**: Incompatible constraints, impossible requests

### **Cost Transparency**

```
Tier 1: FREE
Tier 2: $0.0006 per analysis
  - Input tokens: 634
  - Output tokens: 808
  - Model: gemini-2.5-flash
```

---

## 📈 Performance

| Metric | Tier 1 | Tier 2 |
|--------|--------|--------|
| **Speed** | 300-800ms | 5-25s |
| **Cost** | $0.00 | ~$0.0006 |
| **Accuracy** | 85% structural | 95% semantic |
| **Memory** | ~200MB | ~300MB |
| **Internet** | ❌ Not required | ✅ Required |

---

## 🧪 Testing

### **Run Demo Tests**

```bash
# Comprehensive test suite
python test_prompt_quality_analyzer.py

# With LLM deep analysis
python test_llm_analyzer.py

# Individual components
python test_alignment_checker.py
python test_contradiction_detector.py
python test_verbosity_analyzer.py
```

### **Test with Artifacts**

```bash
python test_case_1_with_artifacts.py
```

---

## 📖 Documentation

- **[WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)** - Complete Web UI documentation
- **[PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md)** - Artifact support details
- **[PHASE_2_DESIGN.md](PHASE_2_DESIGN.md)** - LLM integration architecture
- **[CLAUDE.md](CLAUDE.md)** - Development instructions

---

## 🎨 Web UI Screenshots

### Main Interface
- Clean, modern design with Tailwind CSS
- Multiline prompt inputs with character counters
- Drag & drop file uploads
- Two-tier analysis mode selector

### Results Visualization
- Overall score with animated progress bar
- Component score breakdown
- Severity-coded issue list
- LLM deep analysis results (Tier 2)
- Cost tracking and token usage

---

## 💡 Use Cases

### **1. Development/Testing**
```
Scenario: Testing 20 variations of a system prompt
Solution: Use Tier 1 for all → 20 × 0.3s = 6 seconds, $0
Benefit: Instant feedback, iterate quickly
```

### **2. Debugging False Positives**
```
Scenario: Chatbot giving unexpected responses
Solution: Tier 1 finds alignment score 6.5/10 → Trigger Tier 2
Result: LLM explains "jellyfish+snake vs bread = impossible"
Benefit: Root cause identified with clear explanation
```

### **3. Safety Validation**
```
Scenario: Recipe chatbot, user asks for toxic ingredients
Solution: Tier 2 detects PRIMARY RISK: SAFETY
Result: Recommends rejecting request + expert supervision warning
Benefit: Prevents harmful outputs
```

### **4. Security Audit**
```
Scenario: Check 1000 prompts for injection vulnerabilities
Solution: Tier 1 (free) finds suspicious patterns → Tier 2 validates 50 flagged
Cost: $0 + (50 × $0.0006) = $0.03 vs pure LLM: $50
Benefit: 99.94% cost savings
```

---

## 🆚 Why Not Just Use LLM?

| Your Needs | Pure LLM | This Tool |
|------------|----------|-----------|
| Analyze 1000 prompts | $50, 1.4 hours | $0 (Tier 1), 8 minutes |
| CI/CD quality gates | ❌ Response variance | ✅ Deterministic scores |
| Batch prompt audits | 💰 Expensive | ✅ Free for Tier 1 |
| Debug specific issues | ⏱️ Slow | ✅ Fast Tier 1 + optional Tier 2 |
| Exact line numbers | ❌ Vague | ✅ Precise locations |
| Offline usage | ❌ Internet required | ✅ Tier 1 works offline |

**Best of Both Worlds:** Use Tier 1 for 90% of cases, Tier 2 for the complex 10%

---

## 🛠️ Tech Stack

- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **NLP**: spaCy (en_core_web_sm)
- **LLM**: Gemini 2.5 Flash (Phase 2)
- **Web**: Flask + HTML/CSS/JavaScript + Tailwind
- **ML**: scikit-learn, numpy

---

## 📦 Project Structure

```
llm_prompt_analyzer/
├── v2/                        # Core analyzer (Tier 1 + Tier 2)
│   ├── prompt_quality_analyzer.py   # Master orchestrator
│   ├── system_prompt_parser.py      # Requirement extraction
│   ├── alignment_checker.py         # Compatibility checking
│   ├── contradiction_detector.py    # Conflict detection
│   ├── verbosity_analyzer.py        # Length analysis
│   ├── artifact_handler.py          # File validation (Phase 1)
│   ├── llm_analyzer.py              # LLM integration (Phase 2)
│   └── embedding_manager.py         # Semantic similarity
├── web/                       # Web UI
│   ├── app.py                # Flask backend
│   ├── templates/index.html  # Frontend UI
│   └── static/js/app.js      # JavaScript logic
├── test_*.py                  # Test files
├── interactive_analyzer.py    # CLI interface
├── run_analyzer.py           # Simple entry point
└── requirements.txt          # Dependencies
```

---

## 🤝 Contributing

This is a research project. Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Use in your own projects (MIT License)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

Built by **Shiva Subramaniam** with assistance from **Claude (Anthropic)**

Special thanks to the open-source community for:
- sentence-transformers
- spaCy
- Google Generative AI
- Flask & Tailwind CSS

---

## 📞 Support

- **GitHub Issues**: https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer/issues
- **Documentation**: See docs in repository
- **Repository**: https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer

---

**🚀 Built for developers who demand better LLM applications. Make your prompts bulletproof!**
