"""
Test Suite for SystemPromptParser

Demonstrates extraction of requirements from various system prompts.
"""

from v2.embedding_manager import EmbeddingManager, EmbeddingConfig
from v2.system_prompt_parser import (
    SystemPromptParser,
    print_system_prompt_analysis,
    RequirementType
)


def test_flight_booking_system():
    """Test with a flight booking system prompt"""
    print("\n" + "="*70)
    print("TEST 1: FLIGHT BOOKING SYSTEM")
    print("="*70)

    system_prompt = """
You are a flight booking assistant that helps users find and book flights.

REQUIRED INFORMATION:
- Origin city (departure location)
- Destination city (arrival location)
- Travel date or date range

OPTIONAL INFORMATION:
- Preferred departure time
- Budget or price range
- Airline preference

MUST:
- Always verify all booking details before confirming
- Provide accurate flight information
- Never share user payment information with third parties

SHOULD:
- Prefer direct flights when available
- Recommend flights within user's budget

You cannot provide medical advice or legal guidance.
Keep responses professional and concise.
"""

    # Parse
    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)
    print_system_prompt_analysis(analysis)

    # Validate
    print("\n[VALIDATION]")
    print(f"Expected domain: flight_booking | Actual: {analysis.domain}")
    print(f"Expected required params: 3 | Actual: {len(analysis.required_parameters)}")
    print(f"Expected hard constraints: >=3 | Actual: {len(analysis.hard_constraints)}")
    print(f"Expected soft constraints: >=2 | Actual: {len(analysis.soft_constraints)}")

    return analysis


def test_nutrition_bot_system():
    """Test with a nutrition bot system prompt"""
    print("\n\n" + "="*70)
    print("TEST 2: NUTRITION BOT SYSTEM")
    print("="*70)

    system_prompt = """
You are a nutrition bot for children aged 6-12.

REQUIRED INFORMATION:
- Child's age
- Dietary restrictions or allergies
- Meal type (breakfast, lunch, dinner, snack)

MUST:
- Suggest healthy, age-appropriate recipes
- Never suggest recipes with common allergens if restrictions are mentioned
- Avoid recipes with added sugars >10g per serving
- Always include nutritional information

NEVER:
- Suggest recipes with soda, candy, or highly processed foods
- Recommend dietary supplements without parental consultation
- Provide medical advice

SHOULD:
- Prefer recipes with vegetables and whole grains
- Recommend fun, colorful presentations for kids

You cannot diagnose allergies or medical conditions.
Responses should be friendly and encouraging.
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)
    print_system_prompt_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Domain: {analysis.domain}")
    print(f"Required parameters: {len(analysis.required_parameters)}")
    print(f"Hard constraints: {len(analysis.hard_constraints)}")
    print(f"Safety guidelines: {len(analysis.safety_guidelines)}")

    return analysis


def test_image_generation_system():
    """Test with an image generation system prompt"""
    print("\n\n" + "="*70)
    print("TEST 3: IMAGE GENERATION SYSTEM")
    print("="*70)

    system_prompt = """
You are a brand image generator for professional businesses.

REQUIRED INFORMATION:
- Image description or concept
- Target style (modern, classic, minimalist, bold)
- Primary color preferences

OPTIONAL INFORMATION:
- Specific dimensions
- Brand guidelines or references
- Secondary colors

MUST:
- Generate professional, high-quality images
- Always respect copyright and trademark guidelines
- Never create images with harmful, offensive, or inappropriate content
- Maintain brand consistency across requests

SHOULD:
- Prefer simple, clean designs for brand images
- Recommend color combinations that work well together

FORMAT:
- Respond with image generation parameters in JSON format
- Include rationale for design choices

You cannot generate images of real people or copyrighted characters.
All outputs must be original and commercially safe.
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)
    print_system_prompt_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Domain: {analysis.domain}")
    print(f"Required parameters: {len(analysis.required_parameters)}")
    print(f"Output format expectations: {len(analysis.output_formats)}")
    print(f"Scope definitions: {len(analysis.scope_definitions)}")

    return analysis


def test_customer_support_system():
    """Test with a customer support system prompt"""
    print("\n\n" + "="*70)
    print("TEST 4: CUSTOMER SUPPORT SYSTEM")
    print("="*70)

    system_prompt = """
You are a customer support assistant for an e-commerce platform.

Your role is to help customers with orders, returns, and account issues.

MUST:
- Always verify customer identity before accessing account information
- Never share sensitive payment details
- Provide accurate order status information
- Escalate complex issues to human agents

SHOULD:
- Respond empathetically to customer concerns
- Offer solutions proactively
- Keep response time under 2 minutes

NEVER:
- Make unauthorized refunds or account changes
- Share customer information with third parties
- Provide financial or legal advice

You can access order history, tracking information, and account settings.
You cannot modify payment methods or shipping addresses without verification.

Keep responses friendly, professional, and under 150 words.
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)
    print_system_prompt_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Domain: {analysis.domain}")
    print(f"Total requirements: {analysis.total_requirements}")
    print(f"Hard constraints: {len(analysis.hard_constraints)}")
    print(f"Safety guidelines: {len(analysis.safety_guidelines)}")

    return analysis


def test_minimal_system_prompt():
    """Test with a minimal system prompt"""
    print("\n\n" + "="*70)
    print("TEST 5: MINIMAL SYSTEM PROMPT")
    print("="*70)

    system_prompt = """
You are a helpful assistant. Answer user questions accurately and concisely.
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)
    print_system_prompt_analysis(analysis)

    print("\n[VALIDATION]")
    print(f"Domain: {analysis.domain}")
    print(f"Total requirements: {analysis.total_requirements}")
    print(f"Primary objective: {analysis.primary_objective}")

    return analysis


def test_parameter_detection():
    """Focused test on parameter detection accuracy"""
    print("\n\n" + "="*70)
    print("TEST 6: PARAMETER DETECTION ACCURACY")
    print("="*70)

    system_prompt = """
You are a flight booking assistant.

REQUIRED:
- Origin city or airport
- Destination city or airport
- Departure date
- Number of passengers

OPTIONAL:
- Return date
- Preferred airline
- Budget range
- Seat preference
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)

    print(f"\nRequired Parameters Detected: {len(analysis.required_parameters)}")
    for param in analysis.required_parameters:
        print(f"  - {param.name}: {param.description} (confidence: {param.confidence:.2%})")

    print(f"\nOptional Parameters Detected: {len(analysis.optional_parameters)}")
    for param in analysis.optional_parameters:
        print(f"  - {param.name}: {param.description} (confidence: {param.confidence:.2%})")

    # Check specific parameters
    print("\n[VALIDATION]")
    has_origin = analysis.has_parameter("origin")
    has_destination = analysis.has_parameter("destination")
    has_date = analysis.has_parameter("date")

    print(f"Has 'origin': {has_origin}")
    print(f"Has 'destination': {has_destination}")
    print(f"Has 'date': {has_date}")

    if has_origin and has_destination and has_date:
        print("[PASS] Core flight booking parameters detected!")
    else:
        print("[FAIL] Missing core flight booking parameters")

    return analysis


def test_constraint_classification():
    """Test classification of hard vs soft constraints"""
    print("\n\n" + "="*70)
    print("TEST 7: CONSTRAINT CLASSIFICATION")
    print("="*70)

    system_prompt = """
You are an AI assistant.

MUST:
- Always verify sources before providing information
- Never share user data with third parties
- Provide accurate, factual responses

SHOULD:
- Prefer concise answers over lengthy explanations
- Recommend additional resources when helpful
- Try to anticipate follow-up questions

NEVER:
- Generate harmful or offensive content
- Impersonate real individuals
- Provide medical or legal advice
"""

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    parser = SystemPromptParser(embedding_manager)

    analysis = parser.parse(system_prompt)

    print(f"\nHard Constraints: {len(analysis.hard_constraints)}")
    for constraint in analysis.hard_constraints:
        polarity_str = f"({constraint.polarity.value})" if constraint.polarity else ""
        print(f"  - {polarity_str} {constraint.content[:60]}...")

    print(f"\nSoft Constraints: {len(analysis.soft_constraints)}")
    for constraint in analysis.soft_constraints:
        polarity_str = f"({constraint.polarity.value})" if constraint.polarity else ""
        print(f"  - {polarity_str} {constraint.content[:60]}...")

    print("\n[VALIDATION]")
    print(f"Expected hard constraints: 6 | Actual: {len(analysis.hard_constraints)}")
    print(f"Expected soft constraints: 3 | Actual: {len(analysis.soft_constraints)}")

    # Check polarity detection
    negative_constraints = [c for c in analysis.hard_constraints if c.polarity and c.polarity.value == "negative"]
    positive_constraints = [c for c in analysis.hard_constraints if c.polarity and c.polarity.value == "positive"]

    print(f"Negative constraints: {len(negative_constraints)}")
    print(f"Positive constraints: {len(positive_constraints)}")

    return analysis


def run_all_tests():
    """Run all SystemPromptParser tests"""
    print("\n" + "="*70)
    print("SYSTEM PROMPT PARSER - COMPREHENSIVE TEST SUITE")
    print("="*70)

    try:
        # Run all tests
        test_flight_booking_system()
        test_nutrition_bot_system()
        test_image_generation_system()
        test_customer_support_system()
        test_minimal_system_prompt()
        test_parameter_detection()
        test_constraint_classification()

        print("\n\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
