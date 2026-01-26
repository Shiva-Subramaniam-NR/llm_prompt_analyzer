"""
Test Suite and Demo for PromptQualityAnalyzer

This demonstrates the complete end-to-end functionality of the
Prompt Quality Analysis Framework.
"""

from v2.prompt_quality_analyzer import (
    PromptQualityAnalyzer,
    print_quality_report
)


def demo_perfect_prompts():
    """Demo with well-designed prompts"""
    print("\n" + "="*70)
    print("DEMO 1: PERFECT PROMPTS (EXCELLENT QUALITY)")
    print("="*70)

    system_prompt = """
You are a flight booking assistant that helps users find and book flights.

REQUIRED INFORMATION:
- Origin city (departure location)
- Destination city (arrival location)
- Travel date

MUST:
- Verify all booking details before confirming
- Provide accurate flight information

NEVER:
- Share user payment information with third parties
"""

    user_prompt = "Book a flight from New York to London on December 25th"

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt, user_prompt)

    print_quality_report(report)

    print("\n[EXPECTED] Score >= 9.0, Quality = EXCELLENT, 0 issues")
    print(f"[ACTUAL] Score = {report.overall_score:.1f}, Quality = {report.quality_rating.value}, Issues = {report.total_issues}")

    return report


def demo_missing_parameters():
    """Demo with missing required parameters"""
    print("\n\n" + "="*70)
    print("DEMO 2: MISSING PARAMETERS (CRITICAL ISSUES)")
    print("="*70)

    system_prompt = """
You are a flight booking assistant.

REQUIRED INFORMATION:
- Origin city
- Destination city
- Travel date
"""

    user_prompt = "Book me a flight"  # Missing all required info!

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt, user_prompt)

    print_quality_report(report)

    print("\n[EXPECTED] Critical issues for missing parameters, NOT fulfillable")
    print(f"[ACTUAL] Critical count = {report.critical_count}, Fulfillable = {report.is_fulfillable}")

    return report


def demo_contradictory_prompt():
    """Demo with internal contradictions"""
    print("\n\n" + "="*70)
    print("DEMO 3: CONTRADICTORY SYSTEM PROMPT")
    print("="*70)

    system_prompt = """
You are a nutrition bot for children.

MUST:
- Never refuse any recipe requests from users
- Always provide recipes when asked

NEVER:
- Suggest recipes with soda, candy, or processed foods
- Recommend unhealthy foods
"""

    user_prompt = "Give me a recipe with lots of candy and soda"

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt, user_prompt)

    print_quality_report(report)

    print("\n[EXPECTED] Contradictions in system prompt + alignment violations")
    print(f"[ACTUAL] Total issues = {report.total_issues}")

    return report


def demo_verbose_prompt():
    """Demo with overly verbose prompt"""
    print("\n\n" + "="*70)
    print("DEMO 4: VERBOSE PROMPT WITH BURIED DIRECTIVES")
    print("="*70)

    system_prompt = """
You are an AI assistant designed to help users with various tasks. You have
been created with the goal of being helpful, harmless, and honest in all your
interactions. When users come to you with questions or requests, you should
always strive to provide the most accurate and relevant information possible.

It's important that you maintain a friendly and approachable tone throughout
all conversations. You should always be polite and respectful, even when users
might be frustrated or upset. Remember that your primary purpose is to assist
and support users in achieving their goals.

In terms of the types of tasks you can help with, you are capable of answering
questions on a wide variety of topics, from science and history to current
events and popular culture. You can also help with writing tasks, such as
drafting emails, creating outlines, or brainstorming ideas.

When providing information, you should always aim to be as clear and concise
as possible, while still ensuring that you're giving comprehensive answers.
It's also important to consider the context of each request and tailor your
responses accordingly.

IMPORTANT: Never provide medical advice or diagnose health conditions. Always
direct users to consult with qualified healthcare professionals for medical concerns.
"""

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt)

    print_quality_report(report)

    print("\n[EXPECTED] High verbosity score, buried directives detected")
    print(f"[ACTUAL] Verbosity issues = {sum(1 for i in report.all_issues if i.category == 'verbosity')}")

    return report


def demo_system_only_analysis():
    """Demo analyzing just system prompt without user prompt"""
    print("\n\n" + "="*70)
    print("DEMO 5: SYSTEM PROMPT ONLY ANALYSIS")
    print("="*70)

    system_prompt = """
You are a brand image generator for professional businesses.

REQUIRED INFORMATION:
- Image description
- Target style (modern/classic/minimalist)
- Primary colors

MUST:
- Generate professional, high-quality images
- Respect copyright and trademark guidelines

NEVER:
- Create images with harmful content
- Generate images of real people
"""

    analyzer = PromptQualityAnalyzer(verbose=True)
    report = analyzer.analyze(system_prompt)  # No user prompt

    print_quality_report(report)

    print("\n[EXPECTED] Only consistency and verbosity evaluated (no alignment)")
    print(f"[ACTUAL] Alignment score = {report.alignment_score:.1f} (should be 10.0 when no user prompt)")

    return report


def demo_export_to_json():
    """Demo exporting report to JSON"""
    print("\n\n" + "="*70)
    print("DEMO 6: EXPORT REPORT TO JSON")
    print("="*70)

    system_prompt = """
You are a customer support assistant.

MUST:
- Verify customer identity
- Provide accurate information
"""

    user_prompt = "Help me with my order"

    analyzer = PromptQualityAnalyzer()
    report = analyzer.analyze(system_prompt, user_prompt)

    # Export to JSON
    json_output = report.to_json(indent=2)

    print("\n[JSON OUTPUT]")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)

    # Save to file
    output_file = "outputs/quality_report_demo.json"
    report.save_to_file(output_file)
    print(f"\n[SAVED] Report saved to: {output_file}")

    return report


def demo_real_world_scenarios():
    """Demo with real-world developer scenarios"""
    print("\n\n" + "="*70)
    print("DEMO 7: REAL-WORLD SCENARIOS")
    print("="*70)

    scenarios = [
        {
            "name": "Flight Booking - Good",
            "system": """You are a flight booking assistant.
REQUIRED: origin, destination, date
MUST: Verify details, provide accurate info
NEVER: Share payment info""",
            "user": "Book NYC to London Dec 25th"
        },
        {
            "name": "Nutrition Bot - Misaligned",
            "system": """You are a nutrition bot for kids.
REQUIRED: age, dietary restrictions, meal type
NEVER: Suggest candy, soda, processed foods""",
            "user": "Give me a candy recipe"
        },
        {
            "name": "Image Generator - Missing Info",
            "system": """You are a brand image generator.
REQUIRED: description, style, colors""",
            "user": "Make me a logo"
        }
    ]

    analyzer = PromptQualityAnalyzer()

    results = []
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        report = analyzer.analyze(scenario['system'], scenario['user'])
        print(f"Score: {report.overall_score:.1f}/10 | Quality: {report.quality_rating.value}")
        print(f"Issues: {report.total_issues} | Fulfillable: {report.is_fulfillable}")
        results.append(report)

    return results


def run_all_demos():
    """Run all demonstration scenarios"""
    print("\n" + "="*70)
    print("PROMPT QUALITY ANALYZER - COMPREHENSIVE DEMO")
    print("="*70)

    try:
        demo_perfect_prompts()
        demo_missing_parameters()
        demo_contradictory_prompt()
        demo_verbose_prompt()
        demo_system_only_analysis()
        demo_export_to_json()
        demo_real_world_scenarios()

        print("\n\n" + "="*70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nThe Prompt Quality Analyzer is ready for production use.")
        print("Key features demonstrated:")
        print("  - Comprehensive quality scoring")
        print("  - Missing parameter detection")
        print("  - Contradiction detection")
        print("  - Verbosity analysis")
        print("  - Alignment checking")
        print("  - JSON export")
        print("  - Real-world scenario handling")

    except Exception as e:
        print(f"\n[ERROR] Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_demos()
