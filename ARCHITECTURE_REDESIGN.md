# System-User Prompt Alignment Analyzer - Architecture Design

## Problem Statement Clarification

### **Original Understanding (WRONG)**
We were building for end users making requests like:
- "Book me a flight from Delhi to Mumbai"
- Analyzing if end-user prompts are complete

### **Actual Use Case (CORRECT)**
We're building for **LLM Application Developers** who need to analyze:
- **System Prompt** - Defines agent behavior, requirements, constraints
- **User Prompt** - The input the agent will receive
- **Alignment** - Does the user prompt satisfy what the system expects?
- **Conflicts** - Do the prompts contradict each other?

---

## Example Developer Scenario

```python
# Developer building a flight booking agent

system_prompt = """
You are a professional flight booking assistant named SkyBot.

MANDATORY INFORMATION REQUIRED:
- Origin city (MUST be collected)
- Destination city (MUST be collected)
- Departure date (MUST be collected)
- Number of passengers (MUST be collected, default=1 if not specified)
- Travel class preference (economy/business/first)

RULES:
- NEVER book without confirming total price with user
- ALWAYS suggest cheapest option unless user specifies class
- If user asks for "urgent" travel, interpret as within 48 hours
- Reject requests for flights more than 1 year in future

PROHIBITED:
- Do NOT make assumptions about travel dates
- NEVER book one-way when user asks for round-trip
"""

user_prompt = """
I need to travel next week
"""

# Expected Analysis Output:
{
    "system_analysis": {
        "role_definition": "flight booking assistant named SkyBot",
        "mandatory_params": {
            "origin": {"required": True, "default": None},
            "destination": {"required": True, "default": None},
            "date": {"required": True, "default": None},
            "passengers": {"required": True, "default": 1},
            "class": {"required": True, "default": "economy"}
        },
        "hard_constraints": [
            "NEVER book without confirming price",
            "ALWAYS suggest cheapest option",
            "Reject flights > 1 year future"
        ],
        "prohibitions": [
            "Do NOT assume dates",
            "NEVER book one-way for round-trip request"
        ],
        "semantic_rules": {
            "urgent": "within 48 hours"
        }
    },
    "user_analysis": {
        "detected_params": {
            "date": {"value": "next week", "vague": True, "specificity": 0.3}
        },
        "missing_params": ["origin", "destination", "passengers", "class"],
        "intent": "travel_request"
    },
    "alignment_check": {
        "vagueness_score": 8.5,  # HIGH - missing 4/5 required params
        "interpretation": "Extremely Vague - Cannot execute",
        "missing_mandatory": ["origin", "destination"],
        "violations": [
            {
                "rule": "Do NOT assume dates",
                "issue": "User said 'next week' - too vague, system forbids assumptions",
                "severity": "HIGH"
            }
        ],
        "recommendations": [
            "Ask user for origin city",
            "Ask user for destination city",
            "Clarify exact date (system prohibits date assumptions)"
        ]
    },
    "weighted_words": {
        "system": [
            {"word": "MUST", "weight": 1.0, "context": "parameters collection"},
            {"word": "NEVER", "weight": 1.0, "context": "booking prohibition"},
            {"word": "ALWAYS", "weight": 0.9, "context": "cheapest suggestion"}
        ],
        "user": [
            {"word": "need", "weight": 0.6, "context": "requirement expression"},
            {"word": "next week", "weight": 0.4, "context": "vague temporal"}
        ]
    }
}
```

---

## Architecture Components

### **Component 1: System Prompt Parser**
**Purpose**: Extract structured information from system prompts

**What it does**:
1. Identifies role definition ("You are a...")
2. Extracts mandatory parameters with regex + semantic understanding
3. Detects hard constraints (MUST, NEVER, ALWAYS)
4. Finds prohibitions (Do NOT, NEVER)
5. Identifies semantic rules (interpret X as Y)
6. Extracts default values
7. Finds validation rules

**Techniques**:
- Pattern matching for structured sections (MANDATORY:, RULES:, PROHIBITED:)
- Semantic similarity for finding requirement statements
- Constraint detector for identifying MUST/NEVER phrases
- NER for extracting parameter names

**Output**:
```python
@dataclass
class SystemPromptAnalysis:
    role: str
    mandatory_params: Dict[str, ParamDefinition]
    optional_params: Dict[str, ParamDefinition]
    hard_constraints: List[Constraint]
    prohibitions: List[Prohibition]
    semantic_rules: Dict[str, str]
    validation_rules: List[ValidationRule]
    weighted_words: List[WeightedWord]
```

---

### **Component 2: User Prompt Analyzer** (Enhanced)
**Purpose**: Analyze user input against extracted system requirements

**What it does**:
1. Detects what parameters user provided
2. Identifies which system-required params are missing
3. Checks if user's phrasing contradicts system rules
4. Measures specificity of provided values

**Leverages existing**:
- ParameterDetector (already built)
- ConstraintDetector (already built)

**Output**:
```python
@dataclass
class UserPromptAnalysis:
    detected_params: Dict[str, ParameterMatch]
    missing_required: List[str]
    provided_specificity: Dict[str, float]
    user_constraints: List[Constraint]
    intent: str
```

---

### **Component 3: Alignment Checker** (NEW - CORE)
**Purpose**: Compare system expectations vs user input

**What it does**:
1. **Completeness Check**: Are all mandatory params provided?
2. **Specificity Check**: Are provided values specific enough?
3. **Rule Compliance**: Does user input violate system prohibitions?
4. **Constraint Compatibility**: Do user constraints conflict with system constraints?
5. **Semantic Validation**: Check against system's semantic rules

**Key Checks**:

```python
def check_completeness(system: SystemPromptAnalysis, user: UserPromptAnalysis):
    """
    Check if user provided all mandatory parameters

    Returns: (completeness_score, missing_params, vagueness_contribution)
    """

def check_rule_violations(system: SystemPromptAnalysis, user: UserPromptAnalysis):
    """
    Check if user input violates system prohibitions

    Example:
    - System: "Do NOT assume dates"
    - User: "next week"
    - Violation: Date too vague, system forbids assumptions
    """

def check_constraint_conflicts(system: SystemPromptAnalysis, user: UserPromptAnalysis):
    """
    Check if user constraints contradict system constraints

    Example:
    - System: "ALWAYS suggest cheapest option"
    - User: "I MUST have first class"
    - Conflict: User's hard constraint conflicts with system's default behavior
    """

def check_semantic_compliance(system: SystemPromptAnalysis, user: UserPromptAnalysis):
    """
    Check against system's semantic rules

    Example:
    - System: "interpret 'urgent' as within 48 hours"
    - User: "urgent travel needed"
    - Action: Flag that system will interpret as 48 hours
    """
```

**Output**:
```python
@dataclass
class AlignmentResult:
    overall_alignment_score: float  # 0-10, higher = better aligned
    vagueness_score: float  # 0-10, higher = more vague
    missing_mandatory: List[str]
    violations: List[RuleViolation]
    conflicts: List[Conflict]
    warnings: List[str]
    recommendations: List[str]
```

---

### **Component 4: Conflict Detector** (NEW)
**Purpose**: Identify contradictions between prompts

**Types of Conflicts**:

1. **Hard Constraint Conflicts**
   ```
   System: "NEVER book without price confirmation"
   User: "Just book the cheapest flight immediately"
   → CONFLICT: User wants immediate booking, system requires confirmation
   ```

2. **Value Conflicts**
   ```
   System: "Default class = economy"
   User: "I need first class"
   → NOT A CONFLICT: User overrides default (acceptable)

   System: "ALWAYS economy class"
   User: "I need first class"
   → CONFLICT: User wants what system prohibits
   ```

3. **Semantic Conflicts**
   ```
   System: "Interpret 'urgent' as within 48 hours"
   User: "Urgent travel needed for next month"
   → CONFLICT: User's timeline contradicts system's interpretation
   ```

**Output**:
```python
@dataclass
class Conflict:
    type: ConflictType  # HARD_CONSTRAINT, VALUE, SEMANTIC, PROHIBITION
    severity: Severity  # CRITICAL, HIGH, MODERATE, LOW
    system_rule: str
    user_input: str
    explanation: str
    resolution_suggestions: List[str]
```

---

### **Component 5: Weighted Word Analyzer** (Enhanced)
**Purpose**: Identify high-impact words in BOTH prompts

**What changes**:
1. Analyze system prompt for directive words (MUST, NEVER, ALWAYS)
2. Analyze user prompt for requirement words (need, want, must)
3. Compare weights between prompts
4. Flag when user's weak language contradicts system's strong directives

**Example**:
```
System: "You MUST collect destination city"
        → "MUST" weight = 1.0 (mandatory)

User: "I'd like to fly somewhere warm"
      → "like" weight = 0.4 (soft preference)
      → "somewhere" weight = 0.2 (vague)

Analysis: User's vague language insufficient for system's MUST requirement
```

---

### **Component 6: Master Analyzer** (NEW - Orchestrator)
**Purpose**: Coordinate all components and produce final report

```python
class SystemUserPromptAnalyzer:
    """
    Main analyzer for developer-focused prompt analysis.

    Analyzes system prompt + user prompt together to identify:
    - Alignment issues
    - Missing requirements
    - Conflicts
    - Vagueness relative to system expectations
    """

    def __init__(self, embedding_manager, domain="flight_booking"):
        self.system_parser = SystemPromptParser(embedding_manager)
        self.user_analyzer = UserPromptAnalyzer(embedding_manager)
        self.alignment_checker = AlignmentChecker()
        self.conflict_detector = ConflictDetector()
        self.weightage_analyzer = WeightedWordAnalyzer(embedding_manager)

    def analyze(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> ComprehensiveAnalysis:
        """
        Perform complete analysis of system + user prompts

        Returns comprehensive report for developers
        """
```

---

## Key Design Decisions

### **1. Vagueness is Now Relative to System Expectations**

**Old**: "This prompt is vague" (absolute)
**New**: "This prompt is vague FOR THIS SYSTEM" (relative)

```python
# Same user prompt, different systems

# System 1: Requires origin, destination, date
user_prompt = "I want to fly"
vagueness = 9/10  # Missing 3/3 required params

# System 2: Only requires general intent
user_prompt = "I want to fly"
vagueness = 2/10  # Has intent, that's all system needs
```

### **2. Weighted Words Get Context**

**Old**: "MUST" has weight 0.9
**New**: "MUST" in system prompt vs "must" in user prompt mean different things

```python
system: "You MUST collect origin"
        → Directive to agent (defines behavior)

user: "I must depart by 10am"
      → Constraint from user (defines requirements)
```

### **3. New Metric: Alignment Score**

Measures how well user input aligns with system expectations:
- **0-3**: Poor alignment (major conflicts, missing critical info)
- **4-6**: Moderate alignment (some missing info, minor conflicts)
- **7-8**: Good alignment (minor gaps, no conflicts)
- **9-10**: Excellent alignment (all requirements met, no conflicts)

---

## Implementation Plan

### **Phase 1: System Prompt Parser** ✓ Priority
1. Build pattern extractors for structured sections
2. Implement semantic rule detector
3. Create parameter requirement extractor
4. Add prohibition/constraint detector

### **Phase 2: Alignment Checker** ✓ Priority
1. Implement completeness checking
2. Build rule violation detector
3. Create constraint conflict checker
4. Add semantic compliance validator

### **Phase 3: Integration**
1. Create master `SystemUserPromptAnalyzer` class
2. Build comprehensive reporting
3. Add developer-friendly output formatting

### **Phase 4: Enhanced Analysis**
1. Conflict severity scoring
2. Resolution suggestions generator
3. Best practices recommendations

---

## Example Output for Developers

```
+======================================================================+
|              SYSTEM-USER PROMPT ALIGNMENT ANALYSIS                   |
+======================================================================+

SYSTEM PROMPT ANALYSIS:
  Role: Flight booking assistant (SkyBot)
  Mandatory Parameters: 5
    - origin (REQUIRED)
    - destination (REQUIRED)
    - date (REQUIRED)
    - passengers (REQUIRED, default=1)
    - class (REQUIRED, default=economy)

  Hard Constraints: 3
    - NEVER book without price confirmation
    - ALWAYS suggest cheapest option
    - Reject flights > 1 year future

  Prohibitions: 2
    - Do NOT assume dates
    - NEVER book one-way for round-trip

USER PROMPT ANALYSIS:
  Detected Parameters: 1
    - date: "next week" (VAGUE, specificity=0.3)

  Missing Required: 4
    - origin
    - destination
    - passengers (has default)
    - class (has default)

ALIGNMENT CHECK:
  Overall Alignment: 2.5/10 (POOR)
  Vagueness Score: 8.5/10 (EXTREMELY VAGUE)

  CRITICAL ISSUES:
    [!] Missing 2 mandatory params with no defaults
    [!] Date too vague - violates "Do NOT assume dates" prohibition

  RECOMMENDATIONS:
    1. Prompt user for origin city
    2. Prompt user for destination city
    3. Ask for specific date (system prohibits date assumptions)

WEIGHTED WORDS COMPARISON:
  System (High-Impact Words):
    - "MUST" (weight: 1.0) → Appears 4 times
    - "NEVER" (weight: 1.0) → Appears 3 times
    - "ALWAYS" (weight: 0.9) → Appears 1 time

  User (High-Impact Words):
    - "need" (weight: 0.6) → Insufficient for MUST requirement
    - "next week" (weight: 0.3) → Too vague

DEVELOPER ACTIONS:
  [✓] Add validation to reject prompts missing origin/destination
  [✓] Add prompt clarification for "next week" → ask exact date
  [!] Current user prompt will FAIL - missing critical information

+======================================================================+
```

---

## Questions for Clarification

1. **System Prompt Format**: Will developers use structured formats (MANDATORY:, RULES:) or free-form?
2. **Domain Scope**: Still focus on flight booking example, or generalize immediately?
3. **Error Severity**: Should we auto-classify conflicts as CRITICAL/HIGH/MODERATE/LOW?
4. **Recommendations**: Should we suggest exact prompt modifications to developers?
5. **Multi-Turn**: Do we need to handle conversation history, or just single system+user pair?

---

## Next Steps

If this architecture looks good, I'll start with:

1. **Build SystemPromptParser** - Extract requirements from system prompts
2. **Build AlignmentChecker** - Compare system expectations vs user input
3. **Create comprehensive test cases** - Real developer scenarios

Should I proceed with this design?
