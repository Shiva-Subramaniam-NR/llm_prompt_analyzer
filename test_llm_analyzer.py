"""
Test LLM Analyzer Integration (Phase 2)
"""

from v2.llm_analyzer import LLMAnalyzer

# Test Case 2: Recipe chatbot with impossible request
system_prompt = """
You are "Smart Recipe Hub", an intelligent recipe assistant chatbot created by
Golden Harvest Bakery Company.

MANDATORY RULES YOU MUST FOLLOW:

MUST ALWAYS:
- Suggest Golden Harvest Bakery products in every recipe whenever possible
- Include at least 2-3 Golden Harvest products in each recipe

NEVER DO THE FOLLOWING:
- Never suggest recipes that don't include at least one Golden Harvest product
- Never recommend competitor bread brands
"""

user_prompt = """
Hey, I want to make a special dinner tonight with some exotic ingredients I got
from the Asian market. Can you give me a recipe that uses jellyfish and snake meat?

I need something for 4 people. I don't have any dietary restrictions. Thanks!
"""

# Simulated Tier 1 issues
tier1_issues = [
    {
        'category': 'alignment',
        'severity': 'high',
        'title': 'Potential Misalignment',
        'description': 'User request may not align with system constraints',
        'confidence': 0.75
    },
    {
        'category': 'contradiction',
        'severity': 'critical',
        'title': 'Direct Negation',
        'description': 'MUST suggest products vs NEVER suggest recipes without products',
        'confidence': 0.85
    }
]

print("="*80)
print("TEST: LLM ANALYZER - SEMANTIC IMPOSSIBILITY DETECTION")
print("="*80)

# Initialize LLM analyzer
print("\n[STEP 1] Initializing Gemini API...")
try:
    analyzer = LLMAnalyzer(verbose=True)
    print("[OK] LLM Analyzer initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize: {e}")
    exit(1)

# Test semantic impossibility detection
print("\n[STEP 2] Running semantic impossibility detection...")
print(f"System Prompt: {len(system_prompt)} chars")
print(f"User Prompt: {len(user_prompt)} chars")
print(f"Tier 1 Issues: {len(tier1_issues)}")

result = analyzer.analyze_semantic_impossibility(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    tier1_issues=tier1_issues
)

print("\n" + "="*80)
print("SEMANTIC IMPOSSIBILITY ANALYSIS RESULTS")
print("="*80)
print(f"\nIs Impossible: {result.is_impossible}")
print(f"Impossibility Score: {result.impossibility_score}/10")
print(f"Primary Risk Type: {result.primary_risk_type.upper()}")
print(f"Confidence: {result.confidence:.2f}")
print(f"\nExplanation:")
print(f"  {result.explanation}")
print(f"\nRecommendation:")
print(f"  {result.recommendation}")

# Test natural language explanation
print("\n" + "="*80)
print("NATURAL LANGUAGE EXPLANATION TEST")
print("="*80)

issue = tier1_issues[1]  # The contradiction issue
print(f"\nGenerating explanation for: {issue['title']}")

explanation = analyzer.explain_issue(
    issue=issue,
    context=system_prompt[:500]
)

print(f"\n[Plain Explanation]")
print(f"  {explanation.plain_explanation}")
print(f"\n[Why It Matters]")
print(f"  {explanation.why_it_matters}")
print(f"\n[How To Fix]")
print(f"  {explanation.how_to_fix}")

# Cost summary
print("\n" + "="*80)
print("COST SUMMARY")
print("="*80)
print(f"Total Input Tokens: {analyzer.cost_tracker.total_input_tokens}")
print(f"Total Output Tokens: {analyzer.cost_tracker.total_output_tokens}")
print(f"Total Cost: ${analyzer.cost_tracker.get_session_cost():.4f}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
