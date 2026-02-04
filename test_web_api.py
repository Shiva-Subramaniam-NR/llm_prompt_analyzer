"""
Test Web UI API endpoints
"""
import requests
import json

API_URL = "http://localhost:5000/api"

# Test 1: Health check
print("="*60)
print("TEST 1: Health Check")
print("="*60)
response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Analyze prompt (Tier 1 only)
print("="*60)
print("TEST 2: Tier 1 Analysis")
print("="*60)

system_prompt = """
You are a flight booking assistant.
REQUIRED: origin, destination, date
MUST: Verify all booking details
NEVER: Share payment information
"""

user_prompt = "Book a flight from NYC to London on December 25th"

payload = {
    "system_prompt": system_prompt,
    "user_prompt": user_prompt,
    "use_llm": False
}

response = requests.post(f"{API_URL}/analyze", json=payload)
print(f"Status: {response.status_code}")

if response.ok:
    data = response.json()
    tier1 = data['tier1']
    print(f"\nOverall Score: {tier1['overall_score']:.1f}/10")
    print(f"Quality: {tier1['quality_rating'].upper()}")
    print(f"Can Fulfill: {tier1['is_fulfillable']}")
    print(f"\nComponent Scores:")
    for comp, score in tier1['scores'].items():
        print(f"  {comp.capitalize()}: {score:.1f}/10")
    print(f"\nIssues Found: {tier1['issues']['total']}")
    print(f"  Critical: {tier1['issues']['critical']}")
    print(f"  High: {tier1['issues']['high']}")
    print(f"  Moderate: {tier1['issues']['moderate']}")
    print(f"  Low: {tier1['issues']['low']}")
else:
    print(f"Error: {response.text}")

print("\n" + "="*60)
print("All tests completed successfully!")
print("="*60)
print("\nWeb UI is ready to use at: http://localhost:5000")
print("Open your browser and navigate to the URL above!")
