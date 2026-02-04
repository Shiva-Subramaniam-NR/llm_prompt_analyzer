# Complete User Guide - LLM Prompt Quality Analyzer

## 📚 Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Using the Web UI](#using-the-web-ui)
4. [Using the CLI](#using-the-cli)
5. [Programmatic Usage](#programmatic-usage)
6. [Understanding Results](#understanding-results)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- 2GB free disk space
- (Optional) Gemini API key for Tier 2 features

### Step 1: Clone Repository

```bash
git clone https://github.com/Shiva-Subramaniam-NR/llm_prompt_analyzer.git
cd llm_prompt_analyzer
```

### Step 2: Install Core Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 3: Install Optional Dependencies

**For Web UI:**
```bash
pip install -r requirements-web.txt
```

**For LLM Deep Analysis (Tier 2):**
```bash
pip install google-generativeai
```

**For Artifact Processing:**
```bash
pip install pdfplumber Pillow
```

### Step 4: Configure API Key (Optional)

Create `.env` file in root directory:
```
GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://aistudio.google.com/app/apikey

---

## Getting Started

### First Analysis - Quick Test

```python
from v2.prompt_quality_analyzer import PromptQualityAnalyzer

analyzer = PromptQualityAnalyzer()

system_prompt = "You are a helpful assistant."
user_prompt = "Hello!"

report = analyzer.analyze(system_prompt, user_prompt)
print(f"Score: {report.overall_score:.1f}/10")
```

Expected output:
```
Score: 5.2/10
```

Why low? The system prompt is too vague and lacks constraints.

---

## Using the Web UI

### Starting the Server

```bash
cd web
python app.py
```

Open browser to: **http://localhost:5000**

### Interface Overview

#### **Input Section**

1. **System Prompt** (Mandatory)
   - Minimum 10 characters
   - Real-time character counter
   - Supports multiline input
   - Example: Instructions for your AI assistant

2. **User Prompt** (Optional)
   - For testing system-user compatibility
   - Example: Sample user request

3. **Artifacts** (Optional)
   - Drag & drop or click to upload
   - Supported: PDF, TXT, MD, JSON, CSV, JPG, PNG, GIF
   - Max size: 16MB per file
   - Shows filename and size after upload
   - Click ❌ to remove

4. **Analysis Mode**
   - **Tier 1 Only**: Fast, free, structural analysis (recommended)
   - **Tier 1 + Tier 2**: Adds LLM semantic/safety/security analysis (~$0.0006)

#### **Results Section**

1. **Overall Quality Card**
   - Score out of 10
   - Rating badge (EXCELLENT, GOOD, FAIR, POOR, CRITICAL)
   - Visual progress bar
   - Fulfillability status

2. **Component Scores**
   - Alignment, Consistency, Verbosity, Completeness
   - Individual scores with progress bars

3. **Issues List**
   - Color-coded by severity
   - Detailed descriptions
   - Confidence scores
   - Actionable recommendations

4. **Tier 2 Results** (if enabled)
   - Semantic impossibility analysis
   - Risk type (Safety, Security, Semantic, None)
   - Detailed explanation
   - Cost breakdown

#### **Action Buttons**

- **Analyze Prompt**: Run analysis
- **Clear**: Reset all inputs
- **Export JSON**: Download results

### Example Workflow

1. **Paste your system prompt**
   ```
   You are a flight booking assistant.
   REQUIRED: origin, destination, date
   MUST: Verify all booking details
   NEVER: Share payment information
   ```

2. **Add user prompt** (optional)
   ```
   Book a flight from NYC to London on Dec 25th
   ```

3. **Upload artifacts** (optional)
   - booking_policy.pdf
   - terms.txt

4. **Select Tier 1 Only**

5. **Click "Analyze Prompt"**

6. **Review Results**
   - Score: 10.0/10 (EXCELLENT)
   - 0 issues found
   - All components green

7. **Export JSON** (optional)
   - Saves to `prompt_analysis_<timestamp>.json`

---

## Using the CLI

### Interactive Mode

```bash
python run_analyzer.py
```

**Follow prompts:**

1. **Enter System Prompt**
   - Type or paste your prompt
   - Press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) when done

2. **Enter User Prompt?** (y/n)
   - Choose `y` to provide, `n` to skip

3. **Provide Artifacts?** (y/n)
   - Choose `y` to upload files
   - Enter name and path for each file
   - Press Enter with empty name to finish

4. **Select Analysis Mode**
   - 1: Run all analyses
   - 2: System parser only
   - 3: Contradiction detector only
   - 4: Verbosity analyzer only
   - 5: Alignment checker only
   - 6: Custom selection

5. **View Results**
   - Overall score and rating
   - Component scores
   - Detailed issues
   - Recommendations

6. **Save to JSON?** (y/n)
   - Choose filename
   - Saved to `outputs/` directory

### Example Session

```
$ python run_analyzer.py

[STEP 1] SYSTEM PROMPT (Mandatory)
Enter your system prompt:
You are a recipe chatbot.
MUST: Suggest vegetarian options
NEVER: Recommend meat dishes
^Z

[OK] System prompt received (68 characters, 12 words)

[STEP 2] USER PROMPT (Optional)
Enter user prompt? (y/n): y

Enter your user prompt:
Give me a beef steak recipe
^Z

[OK] User prompt received (27 characters, 6 words)

[STEP 3] SELECT ANALYSES TO RUN
1. [Comprehensive] Run ALL analyses (recommended)
...

Enter choice (1-6): 1

[ANALYZING] Running comprehensive quality analysis...
  [1/4] Parsing system prompt...
  [2/4] Detecting contradictions...
  [3/4] Analyzing verbosity...
  [4/4] Checking alignment with user prompt...
[COMPLETE] Analysis finished. Overall Score: 2.8/10

Overall Score: 2.8/10 (POOR)
Can Fulfill Request: NO

Issues Found: 3 (2 Critical, 1 High)

[CRITICAL] Alignment Violation
  User requests beef steak, but system NEVER recommends meat
  → Recommendation: Reject request or relax constraints

...
```

---

## Programmatic Usage

### Basic Analysis

```python
from v2.prompt_quality_analyzer import PromptQualityAnalyzer

# Initialize (one-time, loads models)
analyzer = PromptQualityAnalyzer(verbose=True)

# Analyze
report = analyzer.analyze(
    system_prompt="Your system instructions here",
    user_prompt="User request here"  # optional
)

# Access results
print(f"Score: {report.overall_score:.1f}/10")
print(f"Quality: {report.quality_rating.value}")
print(f"Fulfillable: {report.is_fulfillable}")

# Get issues
for issue in report.all_issues:
    print(f"[{issue.severity.upper()}] {issue.title}")
    print(f"  {issue.description}")
    print(f"  Fix: {issue.recommendation}\n")
```

### With Artifacts

```python
artifacts = {
    'policy_doc': '/path/to/policy.pdf',
    'screenshot': '/path/to/image.png',
    'data_file': '/path/to/data.json'
}

report = analyzer.analyze(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    artifacts=artifacts
)

# Check for artifact issues
artifact_issues = [i for i in report.all_issues if i.category == 'artifact']
if artifact_issues:
    print("Artifact problems detected!")
    for issue in artifact_issues:
        print(f"  - {issue.description}")
```

### With LLM Deep Analysis

```python
from v2.llm_analyzer import LLMAnalyzer

# Tier 1
analyzer = PromptQualityAnalyzer()
report = analyzer.analyze(system_prompt, user_prompt)

# Tier 2 (if score < 7.0 or debugging)
if report.overall_score < 7.0:
    llm = LLMAnalyzer(verbose=True)

    # Prepare tier1 issues
    tier1_issues = [
        {
            'category': i.category,
            'severity': i.severity,
            'title': i.title,
            'description': i.description,
            'confidence': i.confidence
        }
        for i in report.all_issues
    ]

    # Semantic impossibility check
    result = llm.analyze_semantic_impossibility(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tier1_issues=tier1_issues
    )

    print(f"\nTier 2 Deep Analysis:")
    print(f"Impossible: {result.is_impossible}")
    print(f"Risk Type: {result.primary_risk_type}")
    print(f"Score: {result.impossibility_score}/10")
    print(f"Explanation: {result.explanation}")
    print(f"\nCost: ${llm.cost_tracker.get_session_cost():.4f}")
```

### Export to JSON

```python
# Save to file
report.save_to_file('outputs/analysis_report.json')

# Or get JSON string
json_str = report.to_json()

# Or get dictionary
data_dict = report.to_dict()
```

---

## Understanding Results

### Score Interpretation

| Score Range | Rating | Meaning |
|-------------|--------|---------|
| 9.0 - 10.0 | EXCELLENT | Production-ready, no issues |
| 7.0 - 8.9 | GOOD | Minor improvements possible |
| 5.0 - 6.9 | FAIR | Several issues to address |
| 3.0 - 4.9 | POOR | Major problems, needs work |
| 0.0 - 2.9 | CRITICAL | Broken, cannot fulfill |

### Component Scores

**Alignment (0-10)**
- Measures system-user prompt compatibility
- High: User request aligns with system capabilities
- Low: User wants something system can't/won't provide

**Consistency (0-10)**
- Checks for internal contradictions
- High: No conflicting rules
- Low: MUST vs NEVER conflicts, paradoxes

**Verbosity (0-10)**
- Evaluates prompt length and structure
- High: Concise, well-organized
- Low: Too long, critical directives buried

**Completeness (0-10)**
- Verifies required parameters provided
- High: All needed info present
- Low: Missing critical parameters

### Issue Severity

**CRITICAL** (Red)
- Blocks functionality completely
- Must fix before use
- Examples: Direct contradictions, missing required params

**HIGH** (Orange)
- Major quality issues
- Should fix before production
- Examples: Security risks, buried directives

**MODERATE** (Yellow)
- Improvements recommended
- Affects quality but not functionality
- Examples: Verbosity, optimization opportunities

**LOW** (Blue)
- Minor suggestions
- Nice-to-have improvements
- Examples: Style consistency, best practices

### Risk Types (Tier 2)

**SAFETY**
- Dangerous/harmful instructions
- Toxic ingredients, unsafe DIY
- Unqualified medical/financial advice
- **Action**: Reject request

**SECURITY**
- Prompt injection attempts
- Jailbreak patterns
- Instruction override attempts
- **Action**: Add input validation

**SEMANTIC**
- Fundamentally impossible requests
- Incompatible constraints
- **Action**: Relax constraints or reject

**NONE**
- No impossibility detected
- Request is feasible
- **Action**: Proceed normally

---

## Advanced Features

### Batch Analysis

```python
prompts_to_test = [
    ("System 1", "User 1"),
    ("System 2", "User 2"),
    ("System 3", "User 3"),
]

results = []
for system, user in prompts_to_test:
    report = analyzer.analyze(system, user)
    results.append({
        'system': system[:50],
        'score': report.overall_score,
        'fulfillable': report.is_fulfillable,
        'issues': report.total_issues
    })

# Find problematic prompts
problems = [r for r in results if r['score'] < 7.0]
print(f"Found {len(problems)} problematic prompts")
```

### Cost Estimation

```python
# Estimate Tier 2 cost before running
system_tokens = len(system_prompt.split()) * 1.3  # Rough estimate
user_tokens = len(user_prompt.split()) * 1.3

estimated_cost = (
    (system_tokens + user_tokens) / 1000 * 0.00015 +  # Input
    500 / 1000 * 0.0006  # Output (estimated 500 tokens)
)

print(f"Estimated Tier 2 cost: ${estimated_cost:.4f}")
```

### Custom Thresholds

```python
# Set quality gates
MINIMUM_SCORE = 7.0
MAX_CRITICAL_ISSUES = 0

report = analyzer.analyze(system_prompt, user_prompt)

if report.overall_score < MINIMUM_SCORE:
    print(f"⚠️  Score too low: {report.overall_score:.1f}")

if report.critical_count > MAX_CRITICAL_ISSUES:
    print(f"⚠️  Critical issues: {report.critical_count}")
```

---

## Troubleshooting

### Common Issues

#### **"Model not found" error**
```bash
# Solution: Download spaCy model
python -m spacy download en_core_web_sm
```

#### **"GEMINI_API_KEY not found"**
```bash
# Solution: Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

#### **Web UI won't start**
```bash
# Check if port 5000 is in use
netstat -an | findstr :5000  # Windows
lsof -i :5000  # Mac/Linux

# Solution: Kill process or change port in web/app.py
```

#### **LLM analysis fails**
- Check internet connection
- Verify API key is valid
- Ensure `google-generativeai` is installed
- Check API quota/limits

#### **Slow analysis**
- First run is slow (model loading)
- Subsequent runs are fast (cached)
- Consider disabling verbose mode

---

## Best Practices

### 1. **Use Tier 1 First**
Always run Tier 1 before Tier 2. It's free, fast, and catches 85% of issues.

### 2. **When to Use Tier 2**
- Score < 7.0
- Debugging false positives
- Safety-critical applications
- Security audits

### 3. **Prompt Quality Guidelines**

**Good System Prompt:**
```
You are a customer support agent for AcmeCorp.

REQUIRED from user: order_id, issue_type

MUST:
- Verify order exists before proceeding
- Maintain professional tone
- Offer solutions, not just apologies

NEVER:
- Share other customers' information
- Process refunds without manager approval
- Promise delivery dates
```

**Bad System Prompt:**
```
You help customers. Be nice. Don't do bad things.
```

### 4. **Artifact Best Practices**
- Keep files under 16MB
- Use descriptive names
- Reference in prompt: "See policy.pdf for refund rules"
- Don't upload sensitive data

### 5. **Cost Management (Tier 2)**
- Cache repeated analyses
- Batch similar prompts
- Use Tier 2 selectively
- Monitor monthly spend

### 6. **CI/CD Integration**
```python
# In your test suite
def test_prompt_quality():
    report = analyzer.analyze(SYSTEM_PROMPT)
    assert report.overall_score >= 7.0, "Prompt quality too low"
    assert report.critical_count == 0, "Critical issues found"
```

---

## Examples

### Example 1: Perfect Prompt

```python
system = """
You are a flight booking assistant.
REQUIRED: origin, destination, date
MUST: Verify all details before booking
NEVER: Share payment information
"""

user = "Book NYC to London on Dec 25th"

# Result: 10.0/10, EXCELLENT, 0 issues
```

### Example 2: Contradictory Prompt

```python
system = """
You are a recipe chatbot.
MUST: Always suggest vegan recipes
NEVER: Provide recipes without meat
"""

user = "Give me a dinner recipe"

# Result: 2.1/10, CRITICAL
# Issue: Direct contradiction (vegan vs meat)
```

### Example 3: Impossible Request

```python
system = """
You are Smart Recipe Hub by Golden Harvest Bakery.
MUST: Include bread products in every recipe
"""

user = "Give me a jellyfish and snake meat recipe"

# Tier 1: 6.5/10, potential misalignment
# Tier 2: PRIMARY RISK: SAFETY, 9/10 impossibility
# Explanation: Safety risk + semantic impossibility
```

---

## Getting Help

- **Documentation**: See repository docs
- **GitHub Issues**: Report bugs/request features
- **Community**: Check existing issues for solutions

---

**Happy analyzing! Build better LLM applications! 🚀**
