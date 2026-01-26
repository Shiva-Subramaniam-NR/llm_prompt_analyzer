"""
Test Suite for VerbosityAnalyzer

Demonstrates verbosity analysis on various prompt types.
"""

from v2.verbosity_analyzer import VerbosityAnalyzer, print_verbosity_analysis


def test_verbose_prompt():
    """Test with an excessively verbose system prompt"""

    print("""
+======================================================================+
|                   VERBOSITY ANALYZER TEST SUITE                      |
+======================================================================+
""")

    analyzer = VerbosityAnalyzer()

    # Test 1: Extremely Verbose Prompt
    print("\n" + "="*70)
    print("TEST 1: EXTREMELY VERBOSE PROMPT")
    print("="*70)

    verbose_prompt = """
You are an AI assistant designed to help users with various tasks and queries.
You should always be polite and courteous in your responses. When users ask you
questions, you should provide helpful answers that are relevant to their query.
It's important that you maintain a professional tone throughout the conversation.
You should never be rude or dismissive of user requests. If a user asks something
inappropriate, you should politely decline. Remember to always consider the context
of the conversation when formulating your responses. You should aim to be clear
and concise in your communication. However, you should also ensure that you
provide sufficient detail to be helpful. It's a balance between being too brief
and being too verbose. You should also remember to be respectful of all users
regardless of their background or beliefs. Make sure to always double-check your
responses for accuracy. It is important that you provide correct information.
When you are uncertain about something, you should say so rather than guessing.
You should also be mindful of potential biases in your responses. Try to provide
balanced and fair answers to questions. You should avoid making assumptions about
users' intentions or beliefs. Always give users the benefit of the doubt.
Remember that users come from diverse backgrounds and may have different
perspectives. You should respect these differences in your responses. It's also
important to remember that you should never provide medical, legal, or financial
advice unless specifically qualified to do so. These are sensitive topics that
require professional expertise. You should direct users to appropriate
professionals for such matters. Make sure to always maintain user privacy and
confidentiality. Never share user information with others.

IMPORTANT: Never provide medical advice.
"""

    metrics = analyzer.analyze(verbose_prompt)
    print_verbosity_analysis(metrics)

    # Test 2: Optimized Version
    print("\n\n" + "="*70)
    print("TEST 2: OPTIMIZED VERSION (Same intent, less verbose)")
    print("="*70)

    optimized_prompt = """
You are a helpful AI assistant.

MUST:
- Provide accurate, relevant answers
- Maintain professional, respectful tone
- Admit uncertainty rather than guess
- Avoid assumptions about users

NEVER:
- Provide medical, legal, or financial advice
- Be rude or dismissive
- Share user information
- Make biased responses

For inappropriate requests: Politely decline with brief explanation.
"""

    metrics = analyzer.analyze(optimized_prompt)
    print_verbosity_analysis(metrics)

    # Calculate improvement
    verbose_words = 280
    optimized_words = metrics.total_words
    reduction = ((verbose_words - optimized_words) / verbose_words) * 100
    print(f"\n[IMPROVEMENT] {reduction:.0f}% reduction in length, same intent preserved!")

    # Test 3: Buried Directive Problem
    print("\n\n" + "="*70)
    print("TEST 3: BURIED DIRECTIVE PROBLEM")
    print("="*70)

    buried_prompt = """
Welcome to our customer service bot. We're here to help you with all your
questions about our products and services. Our goal is to provide you with
the best possible experience. We value your time and want to make sure you
get the information you need quickly and efficiently. Our team has worked
hard to create this assistant to serve you better. We appreciate your
patience as we continue to improve our services. We are committed to
excellence in customer service. Thank you for choosing our company. We
look forward to assisting you with your needs today. Please feel free to
ask any questions you may have. We're here to help! Our operating hours are
Monday through Friday, 9am to 5pm. We also offer email support for your
convenience. You can reach us at support@example.com. We typically respond
to emails within 24 hours. For urgent matters, please call our hotline.
We appreciate your business and value your feedback.

CRITICAL: Never provide refunds without manager approval. This is mandatory.
"""

    metrics = analyzer.analyze(buried_prompt)
    print_verbosity_analysis(metrics)

    if metrics.buried_directives:
        print("\n[ISSUE] Critical directive buried after 150+ words!")
        print("LLM may miss this important constraint.")

    # Test 4: Redundant Prompt
    print("\n\n" + "="*70)
    print("TEST 4: REDUNDANT PROMPT")
    print("="*70)

    redundant_prompt = """
You should always be helpful. You should always provide helpful responses.
When users ask questions, you should always give helpful answers.

It's important to be polite. Being polite is important. You should always
maintain a polite tone. Politeness is key.

Make sure to be accurate. Ensure accuracy in responses. It's important to
make sure your answers are accurate. Accuracy matters.

Never be rude. Do not be rude to users. Being rude is not acceptable.
You must never be rude.
"""

    metrics = analyzer.analyze(redundant_prompt)
    print_verbosity_analysis(metrics)

    # Test 5: Ideal Concise Prompt
    print("\n\n" + "="*70)
    print("TEST 5: IDEAL CONCISE PROMPT")
    print("="*70)

    ideal_prompt = """
You are a nutrition bot for children aged 6-12.

REQUIRED INFORMATION:
- Child's age
- Dietary restrictions
- Meal type (breakfast/lunch/dinner/snack)

MUST:
- Suggest healthy, age-appropriate recipes
- Include nutritional information
- Avoid recipes with added sugars >10g per serving

NEVER:
- Suggest recipes with soda, candy, or processed foods
- Recommend supplements without parental consultation
- Make medical or dietary treatment recommendations

For vague requests: Ask clarifying questions before suggesting recipes.
"""

    metrics = analyzer.analyze(ideal_prompt)
    print_verbosity_analysis(metrics)

    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nKey Learnings:")
    print("1. Verbose prompts (250+ words) bury critical directives")
    print("2. Redundancy wastes tokens and confuses LLMs")
    print("3. Optimal range: 50-150 words for system prompts")
    print("4. Use structured format (MUST/NEVER) instead of paragraphs")
    print("5. Place critical constraints at the beginning")


if __name__ == "__main__":
    try:
        test_verbose_prompt()
        print("\n[SUCCESS] Verbosity analysis tests completed!\n")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
