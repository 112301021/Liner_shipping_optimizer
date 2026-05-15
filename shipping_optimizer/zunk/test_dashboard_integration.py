"""
Test script to verify dashboard integration with real data
"""

import json
import requests
import webbrowser
from datetime import datetime

# API endpoints
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Test API endpoints
print("=== Dashboard Integration Test ===")
print(f"Timestamp: {datetime.now()}")
print()

# Test 1: Health check
print("1. Testing Backend Health...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200:
        health = response.json()
        print(f"   ✓ Backend is healthy: {health['status']}")
        print(f"   ✓ Connected clients: {health['connected_clients']}")
    else:
        print(f"   ✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error connecting to backend: {e}")

print()

# Test 2: Metrics summary
print("2. Testing Metrics Summary...")
try:
    response = requests.get(f"{BASE_URL}/api/metrics/summary")
    if response.status_code == 200:
        metrics = response.json()['metrics']
        print(f"   ✓ Weekly Profit: ${metrics['weeklyProfit']:,.2f}")
        print(f"   ✓ Annual Profit: ${metrics['annualProfit']:,.2f}")
        print(f"   ✓ Total Services: {metrics['totalServices']}")
        print(f"   ✓ Coverage: {metrics['coveragePercentage']:.2f}%")
        print(f"   ✓ Profit Margin: {metrics['profitMargin']:.2f}%")

        # Verify expected values
        expected_profit = 773704018.1008376
        if abs(metrics['weeklyProfit'] - expected_profit) < 1000:
            print(f"   ✓ Profit matches expected value: ${expected_profit:,.2f}")
        else:
            print(f"   ⚠ Profit differs from expected: ${expected_profit:,.2f}")
    else:
        print(f"   ✗ Metrics check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error getting metrics: {e}")

print()

# Test 3: Regional data
print("3. Testing Regional Data...")
try:
    response = requests.get(f"{BASE_URL}/api/regions/")
    if response.status_code == 200:
        regions = response.json()['regions']
        print(f"   ✓ Total Regions: {regions}")

        # Check each region
        expected_regions = ['asia', 'europe', 'americas', 'middle east', 'africa']
        actual_regions = [r['id'] for r in regions]

        if set(actual_regions) == set(expected_regions):
            print(f"   ✓ All expected regions present")
        else:
            print(f"   ⚠ Region mismatch. Expected: {expected_regions}, Got: {actual_regions}")

        # Check Americas profit (should be highest)
        americas = next((r for r in regions if r['id'] == 'americas'), None)
        if americas and americas['weekly_profit'] > 400000000:
            print(f"   ✓ Americas profit: ${americas['weekly_profit']:,.2f}")
        else:
            print(f"   ⚠ Americas profit lower than expected")

    else:
        print(f"   ✗ Regional data check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error getting regional data: {e}")

print()

# Test 4: Pipeline status
print("4. Testing Pipeline Status...")
try:
    response = requests.get(f"{BASE_URL}/api/pipeline/status")
    if response.status_code == 200:
        status = response.json()['state']
        print(f"   ✓ Pipeline Status: {status['status']}")
        print(f"   ✓ Stages configured: {len(status['stages'])}")
    else:
        print(f"   ✗ Pipeline status check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error getting pipeline status: {e}")

print()

# Test 5: Frontend accessibility
print("5. Testing Frontend Access...")
try:
    response = requests.get(FRONTEND_URL)
    if response.status_code == 200:
        print(f"   ✓ Frontend is accessible at {FRONTEND_URL}")
    else:
        print(f"   ✗ Frontend not accessible: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error connecting to frontend: {e}")

print()

# Test 6: Verify pipeline_output.json exists
print("6. Testing Pipeline Output File...")
try:
    with open('pipeline_output.json', 'r') as f:
        pipeline_data = json.load(f)
        print(f"   ✓ pipeline_output.json exists")
        print(f"   ✓ Status: {pipeline_data.get('status', 'unknown')}")
        print(f"   ✓ Regional results: {len(pipeline_data.get('regional_results', []))}")

        # Check for summary data
        if 'summary' in pipeline_data:
            summary = pipeline_data['summary']
            print(f"   ✓ Summary found with profit: ${summary.get('weekly_profit', 0):,.2f}")
        else:
            print(f"   ⚠ No summary in pipeline output")

except Exception as e:
    print(f"   ✗ Error reading pipeline_output.json: {e}")

print()
print("=== Test Complete ===")
print(f"Frontend URL: {FRONTEND_URL}")
print(f"Backend API: {BASE_URL}/api")
print()
print("Expected Dashboard Values:")
print(f"- Weekly Profit: $773,704,018")
print(f"- Coverage: 59.33%")
print(f"- 5 Regions with individual profits")
print(f"- Use Real Pipeline option should work")

# Optional: Open browser
try:
    webbrowser.open(FRONTEND_URL)
    print(f"\n✓ Opening dashboard in browser...")
except:
    print(f"\n⚠ Could not auto-open browser. Please manually open {FRONTEND_URL}")