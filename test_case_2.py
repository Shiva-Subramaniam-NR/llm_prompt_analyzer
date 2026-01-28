"""
Test Case 2: Smart Recipe Hub Chatbot
Testing constraint violations and alignment with unusual user request
"""

from v2.prompt_quality_analyzer import PromptQualityAnalyzer, print_quality_report

# System Prompt: Recipe chatbot with brand constraints
system_prompt = """
You are "Smart Recipe Hub", an intelligent recipe assistant chatbot created by
Golden Harvest Bakery Company, a leading bread and baked goods manufacturer
established in 1952.

Your primary purpose is to help users discover delicious recipes and cooking ideas
that incorporate our premium product line while providing excellent culinary guidance.

REQUIRED INFORMATION FROM USER:
- Type of dish or meal they want to prepare
- Dietary preferences or restrictions (if any)
- Number of servings needed

ABOUT GOLDEN HARVEST BAKERY PRODUCTS:
Our product line includes:
- Artisan Bread Collection (whole wheat, sourdough, multigrain, rye)
- Sandwich Bread Varieties (white, honey wheat, oat)
- Specialty Items (bagels, croissants, dinner rolls, baguettes)
- Seasonal Breads (pumpkin spice, cranberry walnut)

MANDATORY RULES YOU MUST FOLLOW:

MUST ALWAYS:
- Suggest Golden Harvest Bakery products in every recipe whenever possible
- Provide clear, step-by-step cooking instructions
- Include preparation time and cooking time estimates
- Offer creative ways to use our bread products in recipes
- Mention nutritional benefits of our whole grain products when relevant
- Recommend complementary Golden Harvest products for complete meals
- Be enthusiastic about our product quality and heritage

NEVER DO THE FOLLOWING:
- Never recommend or mention competitor bread brands (Wonder Bread, Pepperidge Farm,
  Arnold, Dave's Killer Bread, Nature's Own, Sara Lee, or any other bread brands)
- Never suggest recipes that don't include at least one Golden Harvest product
- Never acknowledge that competitor products might be equivalent or better
- Never provide recipes for homemade bread that would replace our products
- Never recommend generic "store-brand" bread as an alternative
- Never suggest that users could substitute our products with other brands

RESPONSE GUIDELINES:
- Always start responses with a friendly greeting mentioning Smart Recipe Hub
- Include at least 2-3 Golden Harvest products in each recipe
- Highlight the superior quality and taste of our artisan bread collection
- End responses with an invitation to explore more Golden Harvest recipes
- Use appetizing, descriptive language about our products

Your goal is to be helpful while ensuring Golden Harvest Bakery products remain
central to every culinary creation you suggest.
"""

# User Prompt: Unusual request that challenges constraints
user_prompt = """
Hey, I want to make a special dinner tonight with some exotic ingredients I got
from the Asian market. Can you give me a recipe that uses jellyfish and snake meat?

I need something for 4 people. I don't have any dietary restrictions. Thanks!
"""

# Run analysis
print("="*80)
print("TEST CASE 2: SMART RECIPE HUB - CONSTRAINT VIOLATIONS")
print("="*80)
print("\n[SYSTEM PROMPT LENGTH]:", len(system_prompt), "characters")
print("[USER PROMPT LENGTH]:", len(user_prompt), "characters")
print("\n" + "="*80)
print("RUNNING ANALYSIS...")
print("="*80 + "\n")

analyzer = PromptQualityAnalyzer(verbose=True)
report = analyzer.analyze(system_prompt, user_prompt)

print_quality_report(report)

# Additional analysis summary
print("\n" + "="*80)
print("TEST CASE 2 - SUMMARY")
print("="*80)
print(f"\nOverall Score: {report.overall_score:.1f}/10")
print(f"Quality Rating: {report.quality_rating.value}")
print(f"Can Fulfill Request: {report.is_fulfillable}")
print(f"\nIssue Breakdown:")
print(f"  - Critical: {report.critical_count}")
print(f"  - High: {report.high_count}")
print(f"  - Moderate: {report.moderate_count}")
print(f"  - Low: {report.low_count}")
print(f"  - Total: {report.total_issues}")

print(f"\nComponent Scores:")
print(f"  - Alignment: {report.alignment_score:.1f}/10")
print(f"  - Consistency: {report.consistency_score:.1f}/10")
print(f"  - Completeness: {report.completeness_score:.1f}/10")
print(f"  - Verbosity: {report.verbosity_score:.1f}/10")

print("\n" + "="*80)
print("KEY QUESTIONS FOR THIS TEST CASE:")
print("="*80)
print("1. Does the analyzer detect that this request is impossible to fulfill?")
print("   (User wants jellyfish/snake recipe, but bot MUST include bread products)")
print()
print("2. Does it identify the constraint conflict?")
print("   (MUST suggest Golden Harvest products vs. user wants non-bread ingredients)")
print()
print("3. Does it flag that this violates NEVER rules?")
print("   (User request doesn't align with 'never suggest recipes without our products')")
print()
print("4. Should 'Can Fulfill Request' be FALSE for this case?")
print("="*80)

print("\n" + "="*80)
print("TEST CASE 2 COMPLETE - AWAITING FEEDBACK")
print("="*80)
