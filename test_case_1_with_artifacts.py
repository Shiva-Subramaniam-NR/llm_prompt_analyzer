"""
Test Case 1 WITH ARTIFACTS: Legal Consultant for Nutrition Company
Demonstrating Phase 1 artifact support
"""

from v2.prompt_quality_analyzer import PromptQualityAnalyzer, print_quality_report
import os

# System Prompt: Verbose legal consultant role
system_prompt = """
You are a highly specialized Legal Compliance Consultant for NutriPet Industries.

REQUIRED INFORMATION FROM USER:
- Type of document being reviewed
- Product name and category
- Geographical market where product will be sold

MANDATORY ACTIONS YOU MUST ALWAYS PERFORM:
- Always verify that all nutritional claims are substantiated by credible scientific research
- Must cross-reference all citations against current regulatory databases
- Always check for proper FDA disclaimer language
- Must identify any statements that could be construed as medical claims

CRITICAL PROHIBITIONS - NEVER DO THE FOLLOWING:
- Never approve any document that makes unsubstantiated health claims
- Never allow statements that claim products can replace veterinary medical care
- Never approve use of human-grade food terminology without proper substantiation
"""

# User Prompt: References documents and images
user_prompt = """
Hi, I need you to analyze this nutrition research document for our new premium dog food
product called "VitalBark Pro Maximum Nutrition Formula".

I'm providing the research document (PDF) and the product packaging image that shows
the nutritional panel. The document includes studies about glucosamine effects on
canine joint health.

We're planning to sell this in the US market, specifically targeting California,
Texas, and Florida initially.

Can you review the document and image and let me know if we're legally compliant?
"""

# Artifacts: Create sample files for demonstration
artifacts = {
    'research_document': 'test_research.pdf',  # File doesn't exist - will test error handling
    'packaging_image': 'test_packaging.jpg'     # File doesn't exist - will test error handling
}

# Run analysis
print("="*80)
print("TEST CASE 1 WITH ARTIFACTS: LEGAL CONSULTANT")
print("="*80)
print("\n[SYSTEM PROMPT LENGTH]:", len(system_prompt), "characters")
print("[USER PROMPT LENGTH]:", len(user_prompt), "characters")
print("[ARTIFACTS PROVIDED]:", list(artifacts.keys()))
print("\n" + "="*80)
print("RUNNING ANALYSIS WITH ARTIFACT VALIDATION...")
print("="*80 + "\n")

analyzer = PromptQualityAnalyzer(verbose=True)
report = analyzer.analyze(system_prompt, user_prompt, artifacts=artifacts)

print_quality_report(report)

# Analysis summary
print("\n" + "="*80)
print("ARTIFACT VALIDATION RESULTS")
print("="*80)
print("\n[EXPECTED BEHAVIOR]:")
print("  - Should detect that user mentions 'research document' and 'packaging image'")
print("  - Should flag that artifact files don't exist at provided paths")
print("  - Should create HIGH severity issues for missing artifacts")
print("\n[ACTUAL BEHAVIOR]:")
artifact_issues = [i for i in report.all_issues if i.category == 'artifact']
print(f"  - Artifact issues detected: {len(artifact_issues)}")
for issue in artifact_issues:
    print(f"    • [{issue.severity.upper()}] {issue.description}")

print("\n" + "="*80)
print("TEST CASE 1 WITH ARTIFACTS COMPLETE")
print("="*80)
