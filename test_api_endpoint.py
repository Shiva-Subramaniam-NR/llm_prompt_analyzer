"""
Test the /api/analyze endpoint directly
"""
import requests
import json

# Test data
test_data = {
    "system_prompt": "You are a helpful assistant that provides clear and concise answers.",
    "user_prompt": "Tell me a joke",
    "use_llm": False,
    "verbose": False
}

print("Testing /api/analyze endpoint...")
print(f"Request data: {json.dumps(test_data, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(
        'http://localhost:5000/api/analyze',
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.ok:
        result = response.json()
        print("\n✓ SUCCESS!")
        print(f"\nOverall Score: {result['tier1']['overall_score']}/10")
        print(f"Quality Rating: {result['tier1']['quality_rating']}")
        print(f"Is Fulfillable: {result['tier1']['is_fulfillable']}")
        print(f"\nComponent Scores:")
        for component, score in result['tier1']['scores'].items():
            print(f"  {component.capitalize()}: {score}/10")
        print(f"\nTotal Issues: {result['tier1']['issues']['total']}")
    else:
        print(f"\n✗ FAILED!")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError as e:
    print(f"\n✗ CONNECTION ERROR!")
    print(f"Could not connect to http://localhost:5000")
    print(f"Error: {e}")
    print("\nMake sure Flask server is running:")
    print("  cd web && python app.py")

except Exception as e:
    print(f"\n✗ ERROR!")
    print(f"Error: {e}")
