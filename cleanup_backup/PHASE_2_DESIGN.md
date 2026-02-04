# Phase 2 Design: LLM Deep Analysis Mode

## 🎯 Core Principle: Hybrid Architecture

**Two-Tier System:**
- **Tier 1 (Non-LLM)**: Always runs - fast, deterministic, structured (300ms)
- **Tier 2 (LLM)**: Optional - semantic, explanatory, nuanced (5s)

## 🏗️ Architecture Overview

```
User Input → [Tier 1: Non-LLM Analysis] → [Quick Report]
                        ↓
              (Optional Tier 2 Trigger)
                        ↓
           [LLM Deep Analysis] → [Enhanced Report]
                        ↓
              [Comparison & Insights]
```

## 📦 Components to Build

### 1. **LLM Integration Module** (`v2/llm_analyzer.py`)

**Purpose**: Interface with Gemini 2.5 Pro for deep analysis

**Key Features:**
- Gemini API integration with error handling
- Prompt templates for different analysis types
- Cost tracking and usage monitoring
- Response caching to reduce costs
- Retry logic for API failures

**API Key Management:**
- Environment variable: `GEMINI_API_KEY`
- Config file: `config/llm_config.json`
- Runtime prompt if not set

### 2. **Semantic Impossibility Detector** (`v2/semantic_validator.py`)

**Purpose**: Detect when user request is fundamentally incompatible with system constraints

**Examples:**
- ❌ User wants jellyfish+snake recipe, but system MUST include bread
- ❌ User wants financial advice, but system NEVER provides financial advice
- ❌ User requests medical diagnosis, but system is recipe chatbot

**How it Works:**
1. Non-LLM tier flags potential misalignment (score < 7.0)
2. LLM tier analyzes semantic compatibility
3. Returns: impossibility_score (0-10), explanation, recommendation

### 3. **Natural Language Explainer** (`v2/explanation_generator.py`)

**Purpose**: Convert structured issues into human-readable explanations

**Input:** QualityIssue from Tier 1
```python
QualityIssue(
    category="contradiction",
    severity="critical",
    title="Direct Negation",
    description="similarity: 85%",
    confidence=0.85
)
```

**Output:** Natural language explanation
```
"I found a critical contradiction in your system prompt. On one hand, you
instruct the AI to 'identify medical claims,' but on the other hand, you
say 'never approve documents with medical claims.' This creates confusion
because the AI doesn't know whether to process medical claims or reject
them entirely.

I recommend clarifying whether the AI should: (a) identify and flag medical
claims for human review, or (b) reject any content with medical claims
outright."
```

### 4. **Comparison Engine** (`v2/comparison_engine.py`)

**Purpose**: Compare Tier 1 (non-LLM) vs Tier 2 (LLM) results

**Metrics:**
- Agreement rate (% of issues both detected)
- False positives (Tier 1 detected, LLM says OK)
- False negatives (LLM detected, Tier 1 missed)
- Unique insights from each tier
- Score delta (how much scores differ)

**Use Case:** Help users understand when LLM adds value vs when non-LLM is sufficient

### 5. **Enhanced Artifact Analyzer** (extends Phase 1)

**Purpose**: Use LLM to analyze artifact content semantically

**Features:**
- Extract key claims from PDF documents
- Validate citations and references
- Check if artifact content matches user prompt description
- Identify potential compliance issues in documents

## 🔧 Implementation Plan

### **Step 1: LLM Integration Module**

```python
# v2/llm_analyzer.py

class LLMAnalyzer:
    """Interface for Gemini 2.5 Pro deep analysis"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or config"""
        self.api_key = api_key or self._load_api_key()
        self.cost_tracker = CostTracker()

    def analyze_semantic_impossibility(
        self,
        system_prompt: str,
        user_prompt: str,
        tier1_issues: List[QualityIssue]
    ) -> SemanticImpossibilityResult:
        """Check if user request is fundamentally incompatible"""

    def explain_issue(
        self,
        issue: QualityIssue,
        context: str
    ) -> str:
        """Generate natural language explanation for an issue"""

    def validate_artifact_content(
        self,
        artifact_text: str,
        expected_description: str
    ) -> ArtifactValidationResult:
        """Check if artifact matches description in prompt"""
```

### **Step 2: Prompt Templates**

```python
# v2/llm_prompts.py

SEMANTIC_IMPOSSIBILITY_PROMPT = """
You are analyzing an LLM prompt pair for semantic compatibility.

System Prompt:
{system_prompt}

User Prompt:
{user_prompt}

The non-LLM analyzer detected these potential issues:
{tier1_issues}

Task: Determine if the user's request is FUNDAMENTALLY IMPOSSIBLE given
the system constraints. Not just misaligned, but truly impossible.

Examples of impossibility:
- User wants recipe with jellyfish, but system MUST include bread in every recipe
- User asks for financial advice, but system NEVER provides financial advice

Respond in JSON:
{{
  "is_impossible": true/false,
  "impossibility_score": 0-10,
  "explanation": "Clear explanation of why it's impossible",
  "recommendation": "How to fix (relax constraint or reject request)"
}}
"""

EXPLANATION_PROMPT = """
You are a helpful prompt engineering assistant. Convert this technical
issue into a clear, actionable explanation for a developer.

Issue Details:
Category: {category}
Severity: {severity}
Title: {title}
Description: {description}
Confidence: {confidence}

Context:
{context}

Provide:
1. Plain English explanation of the problem
2. Why it matters
3. Specific recommendation to fix it
"""
```

### **Step 3: Integration with PromptQualityAnalyzer**

```python
# v2/prompt_quality_analyzer.py (updated)

class PromptQualityAnalyzer:
    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        enable_llm: bool = False,  # NEW
        llm_api_key: Optional[str] = None,  # NEW
        verbose: bool = False
    ):
        # Existing initialization...

        # NEW: Optional LLM analyzer
        self.llm_analyzer = None
        if enable_llm:
            from v2.llm_analyzer import LLMAnalyzer
            self.llm_analyzer = LLMAnalyzer(api_key=llm_api_key)

    def analyze(
        self,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        artifacts: Optional[Dict[str, str]] = None,
        use_llm_deep_analysis: bool = False  # NEW
    ) -> PromptQualityReport:
        """
        Tier 1: Always run non-LLM analysis
        Tier 2: Optionally run LLM deep analysis
        """

        # Tier 1: Non-LLM (existing code)
        tier1_report = self._run_tier1_analysis(
            system_prompt, user_prompt, artifacts
        )

        # Tier 2: LLM (optional)
        if use_llm_deep_analysis and self.llm_analyzer:
            tier2_enhancements = self._run_tier2_analysis(
                system_prompt, user_prompt, tier1_report
            )
            return self._merge_reports(tier1_report, tier2_enhancements)

        return tier1_report
```

## 🎮 User Experience

### **Interactive CLI Flow:**

```
[STEP 4] ANALYSIS MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Choose analysis mode:
  1. [Fast] Non-LLM only (300ms, free, structured)
  2. [Deep] LLM enhanced (5s, costs ~$0.05, semantic)
  3. [Compare] Run both and compare results

Enter choice (1-3): 2

[INFO] LLM mode selected. Checking for API key...
[PROMPT] Gemini API key not found. Enter now? (y/n): y
[INPUT] Enter Gemini API key: ********************************

[ANALYZING]
  ✓ Tier 1 complete (280ms) - Found 3 issues
  → Triggering Tier 2 deep analysis...
  ✓ Tier 2 complete (4.2s) - Enhanced analysis ready

[RESULTS]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 3.2/10 → 2.8/10 (LLM adjusted)
Quality: POOR → CRITICAL (LLM detected semantic impossibility)

[TIER 1 DETECTED] 3 issues
[TIER 2 DETECTED] 2 additional issues + 1 semantic impossibility

[NEW] SEMANTIC IMPOSSIBILITY (Score: 9.2/10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your user is asking for a jellyfish and snake recipe, but your
system prompt requires that EVERY recipe must include at least
one Golden Harvest bread product. This is fundamentally impossible
because jellyfish and snake dishes are Asian exotic cuisine that
typically don't incorporate Western bread products.

Recommendation: Either (a) relax the requirement to "suggest bread
when appropriate" instead of "must include in every recipe", or
(b) politely decline exotic requests outside the bread category.

Cost: $0.048 | Time: 4.2s | Tokens: 2,145
```

## 📊 Comparison Mode Output

```
[COMPARISON MODE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

              │  Non-LLM  │  LLM      │  Agreement
──────────────┼───────────┼───────────┼─────────────
Overall Score │  3.2/10   │  2.8/10   │  -0.4
Issues Found  │  5        │  7        │  71%
Time          │  300ms    │  4,200ms  │  14x slower
Cost          │  $0.00    │  $0.048   │  +$0.048

[BOTH DETECTED] (5 issues - 71% agreement)
  ✓ Contradiction: MUST vs NEVER directives
  ✓ Missing parameter: category
  ✓ 2 artifact issues
  ✓ Verbosity issue

[LLM ONLY] (2 unique insights)
  ⊕ Semantic impossibility: jellyfish+snake vs bread requirement
  ⊕ Cultural mismatch: Asian cuisine vs Western bread products

[NON-LLM ONLY] (0 false positives)

[RECOMMENDATION]
For this case, LLM deep analysis added significant value by
detecting semantic impossibility that non-LLM missed. However,
for 71% of issues, the free non-LLM tier was sufficient.

Suggested workflow: Use non-LLM first, trigger LLM only when
score < 7.0 or when debugging specific failures.
```

## 💰 Cost Management

```python
# v2/cost_tracker.py

class CostTracker:
    """Track Gemini API usage and costs"""

    PRICING = {
        'gemini-2.5-pro': {
            'input': 0.00125,   # per 1K tokens
            'output': 0.005     # per 1K tokens
        }
    }

    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """Record API call and calculate cost"""

    def get_session_cost(self) -> float:
        """Total cost for this session"""

    def get_monthly_cost(self) -> float:
        """Total cost this month (from cache)"""
```

## ✅ Success Criteria for Phase 2

1. **LLM Integration Working**
   - ✅ Gemini 2.5 Pro API calls successful
   - ✅ Error handling for API failures
   - ✅ Cost tracking functional

2. **Semantic Impossibility Detection**
   - ✅ Correctly identifies impossible requests (Test Case 2)
   - ✅ Provides clear explanations
   - ✅ Suggests actionable fixes

3. **Natural Language Explanations**
   - ✅ Converts technical issues to plain English
   - ✅ Includes "why it matters" and "how to fix"
   - ✅ Maintains accuracy from Tier 1

4. **Comparison Mode**
   - ✅ Shows agreement rate between tiers
   - ✅ Identifies unique insights from each
   - ✅ Recommends when to use LLM

5. **User Experience**
   - ✅ API key management smooth
   - ✅ Cost displayed before and after
   - ✅ Clear value proposition shown

## 🚀 Ready to Implement?

**First Step:** Create `v2/llm_analyzer.py` with Gemini integration

Shall I proceed with building the LLM integration module?
