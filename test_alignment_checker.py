"""
Test Suite for AlignmentChecker

Demonstrates detection of misalignments between system and user prompts.
"""

from v2.embedding_manager import EmbeddingManager, EmbeddingConfig
from v2.system_prompt_parser import SystemPromptParser
from v2.alignment_checker import (
    AlignmentChecker,
    print_alignment_analysis,
    MisalignmentType,
    MisalignmentSeverity
)


def test_perfect_alignment():
    """Test with perfect alignment - user provides all required info"""
    print("\n" + "="*70)
    print("TEST 1: PERFECT ALIGNMENT")
    print("="*70)

    system_prompt = """
You are a flight booking assistant.

REQUIRED INFORMATION:
- Origin city (departure location)
- Destination city (arrival location)
- Travel date

MUST:
- Verify all booking details before confirming
- Provide accurate flight information
"""

    user_prompt = "Book a flight from New York to London on December 25th"

    # Run alignment check
    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Expected misalignments: 0 | Actual: {len(analysis.misalignments)}")
    print(f"Expected alignment score: >=9.0 | Actual: {analysis.alignment_score.overall_score:.1f}")

    return analysis


def test_missing_required_parameters():
    """Test with missing required parameters"""
    print("\n\n" + "="*70)
    print("TEST 2: MISSING REQUIRED PARAMETERS")
    print("="*70)

    system_prompt = """
You are a flight booking assistant.

REQUIRED INFORMATION:
- Origin city
- Destination city
- Travel date

MUST:
- Always verify booking details
"""

    user_prompt = "Book me a flight from New York"  # Missing destination and date

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Expected CRITICAL misalignments: 2 | Actual: {analysis.critical_count}")
    print(f"Expected completeness score: <5.0 | Actual: {analysis.alignment_score.completeness:.1f}")

    return analysis


def test_constraint_violation():
    """Test with hard constraint violation"""
    print("\n\n" + "="*70)
    print("TEST 3: CONSTRAINT VIOLATION")
    print("="*70)

    system_prompt = """
You are a nutrition bot for children.

MUST:
- Suggest healthy recipes
- Never suggest recipes with soda or candy

NEVER:
- Recommend highly processed foods
"""

    user_prompt = "Give me a recipe with soda and candy for my kid's party"

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Expected HIGH misalignments: >=1 | Actual: {analysis.high_count}")
    print(f"Constraint violations detected: {sum(1 for m in analysis.misalignments if m.type == MisalignmentType.CONSTRAINT_VIOLATION)}")

    return analysis


def test_out_of_scope():
    """Test with out-of-scope request"""
    print("\n\n" + "="*70)
    print("TEST 4: OUT OF SCOPE REQUEST")
    print("="*70)

    system_prompt = """
You are a flight booking assistant.

You can help with:
- Finding flights
- Booking tickets
- Checking flight status

You cannot:
- Provide medical advice
- Give legal guidance
- Book hotels or cars
"""

    user_prompt = "Can you help me book a hotel in Paris?"

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Out-of-scope misalignments: {sum(1 for m in analysis.misalignments if m.type == MisalignmentType.OUT_OF_SCOPE)}")

    return analysis


def test_safety_violation():
    """Test with safety guideline violation"""
    print("\n\n" + "="*70)
    print("TEST 5: SAFETY GUIDELINE VIOLATION")
    print("="*70)

    system_prompt = """
You are a health information assistant.

MUST:
- Provide general health information
- Cite reliable sources

NEVER:
- Provide medical diagnoses
- Recommend specific medications
- Replace professional medical advice

You cannot diagnose medical conditions or prescribe treatments.
"""

    user_prompt = "Can you diagnose my symptoms and tell me what medication to take?"

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Safety violations: {sum(1 for m in analysis.misalignments if m.type == MisalignmentType.UNSAFE_REQUEST)}")

    return analysis


def test_partial_alignment():
    """Test with partial alignment - some params provided"""
    print("\n\n" + "="*70)
    print("TEST 6: PARTIAL ALIGNMENT")
    print("="*70)

    system_prompt = """
You are a nutrition bot.

REQUIRED INFORMATION:
- Child's age
- Dietary restrictions
- Meal type

SHOULD:
- Prefer recipes with vegetables
- Recommend balanced meals
"""

    user_prompt = "I need a healthy lunch recipe for my 8-year-old"
    # Has: age, meal type
    # Missing: dietary restrictions

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Expected alignment score: 5.0-7.5 | Actual: {analysis.alignment_score.overall_score:.1f}")
    print(f"Expected completeness: ~6.7 | Actual: {analysis.alignment_score.completeness:.1f}")

    return analysis


def test_real_world_nutrition_bot():
    """Real-world scenario: nutrition bot with misalignment"""
    print("\n\n" + "="*70)
    print("TEST 7: REAL-WORLD - NUTRITION BOT MISALIGNMENT")
    print("="*70)

    system_prompt = """
You are a nutrition bot for children aged 6-12.

REQUIRED INFORMATION:
- Child's age
- Dietary restrictions or allergies
- Meal type (breakfast/lunch/dinner/snack)

MUST:
- Suggest healthy, age-appropriate recipes
- Never suggest recipes with common allergens if restrictions mentioned
- Avoid recipes with added sugars >10g per serving

NEVER:
- Suggest recipes with soda, candy, or processed foods
- Recommend supplements without parental consultation
"""

    user_prompt = "Give me a fun dessert recipe with lots of candy and soda"

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    analysis = checker.check_alignment(system_prompt, user_prompt)
    print_alignment_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Is fulfillable: {analysis.is_fulfillable()}")
    print(f"Has critical issues: {analysis.has_critical_issues()}")

    return analysis


def test_real_world_brand_generator():
    """Real-world scenario: brand image generator"""
    print("\n\n" + "="*70)
    print("TEST 8: REAL-WORLD - BRAND IMAGE GENERATOR")
    print("="*70)

    system_prompt = """
You are a brand image generator for professional businesses.

REQUIRED INFORMATION:
- Image description or concept
- Target style (modern, classic, minimalist, bold)
- Primary color preferences

MUST:
- Generate professional, high-quality images
- Always respect copyright and trademark guidelines
- Never create images with harmful or inappropriate content

You cannot generate images of real people or copyrighted characters.
"""

    # Good user prompt
    user_prompt_good = "Create a minimalist logo for a tech startup, using blue and white colors"

    # Bad user prompt
    user_prompt_bad = "Generate an image of Mickey Mouse for my company logo"

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)
    checker = AlignmentChecker(embedding_manager, parser)

    print("\n--- Testing GOOD user prompt ---")
    analysis_good = checker.check_alignment(system_prompt, user_prompt_good)
    print(f"Alignment Score: {analysis_good.alignment_score.overall_score:.1f}/10")
    print(f"Misalignments: {len(analysis_good.misalignments)}")

    print("\n--- Testing BAD user prompt ---")
    analysis_bad = checker.check_alignment(system_prompt, user_prompt_bad)
    print(f"Alignment Score: {analysis_bad.alignment_score.overall_score:.1f}/10")
    print(f"Misalignments: {len(analysis_bad.misalignments)}")
    print(f"Out-of-scope violations: {sum(1 for m in analysis_bad.misalignments if m.type == MisalignmentType.OUT_OF_SCOPE)}")

    print("\n[VALIDATION]")
    print(f"Good prompt score should be >7.0: {analysis_good.alignment_score.overall_score >= 7.0}")
    print(f"Bad prompt should have violations: {analysis_bad.has_critical_issues()}")

    return analysis_good, analysis_bad


def run_all_tests():
    """Run all alignment checker tests"""
    print("\n" + "="*70)
    print("ALIGNMENT CHECKER - COMPREHENSIVE TEST SUITE")
    print("="*70)

    try:
        test_perfect_alignment()
        test_missing_required_parameters()
        test_constraint_violation()
        test_out_of_scope()
        test_safety_violation()
        test_partial_alignment()
        test_real_world_nutrition_bot()
        test_real_world_brand_generator()

        print("\n\n" + "="*70)
        print("ALL ALIGNMENT TESTS COMPLETED SUCCESSFULLY")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
