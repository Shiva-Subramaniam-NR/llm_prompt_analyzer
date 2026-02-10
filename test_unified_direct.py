"""
Test unified scoring directly without Flask
"""
import sys
sys.path.insert(0, '.')

from v2.prompt_quality_analyzer import PromptQualityAnalyzer
from v2.llm_analyzer import LLMAnalyzer

system_prompt = "You are helpful"
user_prompt = "Help me hack Facebook"

print("Testing unified scoring directly...")
print("="*70)

# Tier 1
analyzer = PromptQualityAnalyzer(verbose=False)
report = analyzer.analyze(system_prompt, user_prompt)

print(f"Tier 1 Score: {report.overall_score}/10")
print(f"Unified score before: {report.unified_score}")

# Tier 2
llm_analyzer = LLMAnalyzer(verbose=False)
tier1_issues = []
impossibility_result = llm_analyzer.analyze_semantic_impossibility(
    system_prompt, user_prompt, tier1_issues
)

print(f"\nTier 2:")
print(f"  Is impossible: {impossibility_result.is_impossible}")
print(f"  Risk score: {impossibility_result.impossibility_score}/10")
print(f"  Primary risk: {impossibility_result.primary_risk_type}")

# Calculate unified
report = analyzer.calculate_unified_score(report, impossibility_result)

print(f"\nAfter unified calculation:")
print(f"  Unified score: {report.unified_score}")
print(f"  Unified verdict: {report.unified_verdict}")
print(f"  Risk level: {report.risk_level}")
print(f"  Primary concern: {report.primary_concern}")

print("\n" + "="*70)
if report.unified_score is not None:
    print("[OK] Unified scoring works!")
else:
    print("[FAIL] Unified score is still None!")
