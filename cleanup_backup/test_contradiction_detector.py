"""
Test Suite for ContradictionDetector

Demonstrates contradiction detection with various conflict types.
"""

from v2.embedding_manager import EmbeddingManager, EmbeddingConfig
from v2.contradiction_detector import (
    ContradictionDetector,
    print_contradiction_analysis,
    ContradictionType,
    ContradictionSeverity
)


def test_contradiction_detection():
    """Test contradiction detection with various prompt types"""

    print("""
+======================================================================+
|           CONTRADICTION DETECTOR - COMPREHENSIVE TESTS               |
+======================================================================+
""")

    # Initialize
    print("[INFO] Initializing embedding manager and contradiction detector...")
    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    detector = ContradictionDetector(
        embedding_manager,
        conflict_threshold=0.70,
        negation_threshold=0.65
    )

    # Test cases
    test_cases = [
        {
            "name": "Test 1: Direct Negation (CRITICAL)",
            "prompt": """
You are a helpful assistant.

MUST:
- Always verify user credentials before providing information
- Provide accurate answers to all questions

NEVER:
- Skip verification for any users
- Never verify user credentials as it slows down responses
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.CRITICAL
        },
        {
            "name": "Test 2: Behavioral Conflict - Formality (HIGH)",
            "prompt": """
You are a brand image generator assistant.

STYLE GUIDELINES:
- Maintain a formal, professional tone in all communications
- Use conservative, business-appropriate language
- Be casual and friendly with users
- Use emojis and informal expressions to connect with customers
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.HIGH
        },
        {
            "name": "Test 3: Constraint Mismatch - Length (HIGH)",
            "prompt": """
You are a customer support bot.

REQUIREMENTS:
- Keep all responses under 50 words for brevity
- Provide detailed, comprehensive explanations for every query
- Include step-by-step instructions with examples
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.HIGH
        },
        {
            "name": "Test 4: Permission Conflict (HIGH)",
            "prompt": """
You are a nutrition bot for children.

MUST:
- Never refuse any recipe requests from users
- Always provide recipes when asked
- Promote healthy eating habits

NEVER:
- Suggest recipes with soda, candy, or processed foods
- Politely decline requests for unhealthy recipes
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.HIGH
        },
        {
            "name": "Test 5: Multiple Contradictions",
            "prompt": """
You are an AI assistant.

GUIDELINES:
- Always be absolutely certain in your responses
- Never express any doubt or uncertainty
- Provide confident answers at all times
- Admit when you're unsure about something
- Express your limitations clearly
- Say "I don't know" when appropriate
""",
            "expected_contradictions": 2,
            "expected_severity": ContradictionSeverity.CRITICAL
        },
        {
            "name": "Test 6: No Contradictions (Consistent Prompt)",
            "prompt": """
You are a flight booking assistant.

MUST:
- Provide accurate flight information
- Maintain professional tone
- Verify all booking details before confirming

NEVER:
- Share user payment information
- Provide medical or legal advice
- Book flights without user confirmation
""",
            "expected_contradictions": 0,
            "expected_severity": None
        },
        {
            "name": "Test 7: Subtle Behavioral Conflict (MODERATE)",
            "prompt": """
You are a content moderator bot.

BEHAVIOR:
- Be extremely flexible in interpreting content guidelines
- Apply rules strictly and consistently
- Use judgment to adapt to context
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.MODERATE
        },
        {
            "name": "Test 8: Verification Conflict (HIGH)",
            "prompt": """
You are a data processing assistant.

RULES:
- Always double-check all data sources for accuracy
- Verify information from multiple sources before responding
- Skip verification for trusted sources to save time
- Assume correctness for data from internal systems
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.HIGH
        },
        {
            "name": "Test 9: Real-World Example - Nutrition Bot",
            "prompt": """
You are a nutrition bot for children aged 6-12.

REQUIRED INFORMATION:
- Child's age
- Dietary restrictions
- Meal type (breakfast/lunch/dinner/snack)

MUST:
- Suggest healthy, age-appropriate recipes
- Never refuse any recipe requests
- Avoid recipes with added sugars >10g per serving

NEVER:
- Suggest recipes with soda, candy, or processed foods
- Recommend supplements without parental consultation
- Decline recipe requests from users
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.HIGH
        },
        {
            "name": "Test 10: Scope Conflict - Completeness (MODERATE)",
            "prompt": """
You are a documentation assistant.

GUIDELINES:
- Provide minimal explanations to keep docs concise
- Document every edge case and exception in detail
- Keep each section under 100 words
""",
            "expected_contradictions": 1,
            "expected_severity": ContradictionSeverity.MODERATE
        }
    ]

    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'='*70}")
        print(f"{test_case['name']}")
        print(f"{'='*70}")
        print(f"\nPrompt Preview:")
        print(test_case['prompt'][:200] + "..." if len(test_case['prompt']) > 200 else test_case['prompt'])

        try:
            # Detect contradictions
            analysis = detector.detect(test_case['prompt'])

            # Print results
            print_contradiction_analysis(analysis)

            # Validate expectations
            expected_count = test_case['expected_contradictions']
            actual_count = len(analysis.contradictions)

            if actual_count == expected_count:
                print(f"\n[PASS] Detected {actual_count} contradictions (expected {expected_count})")
            else:
                print(f"\n[MISMATCH] Detected {actual_count} contradictions, expected {expected_count}")

            # Check severity if contradictions expected
            if expected_count > 0 and actual_count > 0:
                expected_severity = test_case['expected_severity']
                has_expected_severity = any(
                    c.severity == expected_severity
                    for c in analysis.contradictions
                )

                if has_expected_severity:
                    print(f"[PASS] Found expected severity: {expected_severity.name}")
                else:
                    actual_severities = [c.severity.name for c in analysis.contradictions]
                    print(f"[MISMATCH] Expected severity {expected_severity.name}, got {actual_severities}")

            results.append({
                'test_name': test_case['name'],
                'expected_count': expected_count,
                'actual_count': actual_count,
                'match': actual_count == expected_count,
                'consistency_score': analysis.overall_consistency_score
            })

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in results if r['match'])
    total = len(results)
    accuracy = (passed / total * 100) if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Accuracy: {accuracy:.1f}%")

    print("\nDetailed Results:")
    for r in results:
        status = "[PASS]" if r['match'] else "[FAIL]"
        print(f"{status} {r['test_name']}")
        print(f"   Expected: {r['expected_count']} contradictions | Actual: {r['actual_count']} | Consistency: {r['consistency_score']:.1f}/10")

    print("\n" + "="*70)

    return results


def test_severity_levels():
    """
    Demonstrate how different phrasings result in different contradiction severities.
    """
    print(f"\n\n{'='*70}")
    print("CONTRADICTION SEVERITY COMPARISON")
    print("="*70)
    print("\nDemonstrating how phrasing affects contradiction severity:\n")

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    detector = ContradictionDetector(embedding_manager)

    severity_examples = [
        {
            "name": "CRITICAL - Absolute Negation with 'Always/Never'",
            "prompt": "You must always verify user credentials. Never verify user credentials."
        },
        {
            "name": "HIGH - Strong Behavioral Conflict",
            "prompt": "Maintain a formal, professional tone. Use casual, friendly language with emojis."
        },
        {
            "name": "MODERATE - Partial Conflict",
            "prompt": "Be flexible in applying guidelines. Apply all rules strictly without exceptions."
        },
        {
            "name": "LOW - Minor Tension",
            "prompt": "Be friendly and approachable. Maintain professional boundaries."
        }
    ]

    for example in severity_examples:
        print(f"\n{example['name']}")
        print(f"Prompt: \"{example['prompt']}\"")

        analysis = detector.detect(example['prompt'])

        if analysis.contradictions:
            c = analysis.contradictions[0]
            print(f"  Severity: {c.severity.name} ({c.severity.value})")
            print(f"  Type: {c.type.value}")
            print(f"  Confidence: {c.confidence:.2%}")
            print(f"  Explanation: {c.explanation}")
        else:
            print("  No contradiction detected")

    print("\n" + "="*70)


def test_real_world_scenarios():
    """
    Test with real-world developer scenarios.
    """
    print(f"\n\n{'='*70}")
    print("REAL-WORLD DEVELOPER SCENARIOS")
    print("="*70)

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    embedding_manager = EmbeddingManager(config)
    detector = ContradictionDetector(embedding_manager)

    scenarios = [
        {
            "name": "Scenario 1: Overly Permissive + Safety Rules",
            "prompt": """
You are a customer support chatbot.

BEHAVIOR:
- Never refuse any customer request
- Always help customers achieve their goals
- Accommodate all user needs

SAFETY:
- Decline requests for personal information
- Refuse inappropriate or harmful requests
- Politely reject queries outside your scope
"""
        },
        {
            "name": "Scenario 2: Certainty vs Honesty Trade-off",
            "prompt": """
You are a medical information assistant.

RESPONSE STYLE:
- Provide confident, authoritative answers
- Never express uncertainty or doubt
- Users need clear, definitive guidance

ACCURACY:
- Admit when you don't know something
- Always express limitations clearly
- Indicate when information is uncertain
"""
        },
        {
            "name": "Scenario 3: No Contradictions - Well-Designed Prompt",
            "prompt": """
You are a code review assistant.

MUST:
- Identify security vulnerabilities in code
- Suggest performance improvements
- Explain issues clearly with examples

NEVER:
- Execute or run submitted code
- Make changes without user approval
- Share code with external services

For unclear code: Ask clarifying questions before reviewing.
"""
        }
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 70)

        analysis = detector.detect(scenario['prompt'])

        if analysis.contradictions:
            print(f"\n[ISSUES FOUND] {len(analysis.contradictions)} contradiction(s) detected:")
            print(f"Consistency Score: {analysis.overall_consistency_score:.1f}/10")

            for i, c in enumerate(analysis.contradictions, 1):
                print(f"\n  {i}. [{c.severity.name}] {c.type.value}")
                print(f"     Statement 1: \"{c.statement1[:80]}...\"")
                print(f"     Statement 2: \"{c.statement2[:80]}...\"")
                print(f"     Explanation: {c.explanation}")
        else:
            print(f"\n[SUCCESS] No contradictions detected!")
            print(f"Consistency Score: {analysis.overall_consistency_score:.1f}/10")
            print("This prompt is internally consistent and ready to use.")

    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        # Run main contradiction detection tests
        print("\n" + "="*70)
        print("STARTING CONTRADICTION DETECTOR TEST SUITE")
        print("="*70)

        results = test_contradiction_detection()

        # Run severity comparison
        test_severity_levels()

        # Run real-world scenarios
        test_real_world_scenarios()

        print("\n[SUCCESS] All contradiction detection tests completed!\n")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
