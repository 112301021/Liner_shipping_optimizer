"""
Simple test to verify dashboard integration with real data
"""

import json
import requests
import webbrowser
from datetime import datetime

# API endpoints
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

print("=== Dashboard Integration Test ===")
print(f"Timestamp: {datetime.now()}")
print()

# Test 1: Health check
print("1. Testing Backend Health...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200:
        health = response.json()
        print(f"   [OK] Backend is healthy: {health['status']}")
        print(f"   [OK] Connected clients: {health['connected_clients']}")
    else:
        print(f"   [FAIL] Health check failed: {response.status_code}")
except Exception as e:
    print(f"   [FAIL] Error connecting to backend: {e}")

print()

# Test 2: Metrics summary
print("2. Testing Metrics Summary...")
try:
    response = requests.get(f"{BASE_URL}/api/metrics/summary")
    if response.status_code == 200:
        metrics = response.json()['metrics']
        print(f"   [OK] Weekly Profit: ${metrics['weeklyProfit']:,.2f}")
        print(f"   [OK] Annual Profit: ${metrics['annualProfit']:,.2f}")
        print(f"   [OK] Total Services: {metrics['totalServices']}")
        print(f"   [OK] Coverage: {metrics['coveragePercentage']:.2f}%")
        print(f"   [OK] Profit Margin: {metrics['profitMargin']:.2f}%")

        # Verify expected values
        expected_profit = 773704018.1008376
        if abs(metrics['weeklyProfit'] - expected_profit) < 1000:
            print(f"   [OK] Profit matches expected value: ${expected_profit:,.2f}")
        else:
            print(f"   [WARN] Profit differs from expected: ${expected_profit:,.2f}")
    else:
        print(f"   [FAIL] Metrics check failed: {response.status_code}")
except Exception as e:
    print(f"   [FAIL] Error getting metrics: {e}")

print()

# Test 3: Regional data
print("3. Testing Regional Data...")
try:
    response = requests.get(f"{BASE_URL}/api/regions/")
    if response.status_code == 200:
        regions = response.json()['regions']
        print(f"   [OK] Total Regions: {len(regions)}")

        # Check each region
        region_names = [r['id'] for r in regions]
        print(f"   [OK] Regions: {', '.join(region_names)}")

        # Check Americas profit (should be highest)
        americas = next((r for r in regions if r['id'] == 'americas'), None)
        if americas:
            print(f"   [OK] Americas profit: ${americas['weekly_profit']:,.2f}")
            print(f"   [OK] Americas coverage: {americas['coverage_percent']:.2f}%")

        # Check Asia
        asia = next((r for r in regions if r['id'] == 'asia'), None)
        if asia:
            print(f"   [OK] Asia profit: ${asia['weekly_profit']:,.2f}")
            print(f"   [OK] Asia coverage: {asia['coverage_percent']:.2f}%")

    else:
        print(f"   [FAIL] Regional data check failed: {response.status_code}")
except Exception as e:
    print(f"   [FAIL] Error getting regional data: {e}")

print()

# Test 4: Frontend accessibility
print("4. Testing Frontend Access...")
try:
    response = requests.get(FRONTEND_URL)
    if response.status_code == 200:
        print(f"   [OK] Frontend is accessible at {FRONTEND_URL}")
    else:
        print(f"   [FAIL] Frontend not accessible: {response.status_code}")
except Exception as e:
    print(f"   [FAIL] Error connecting to frontend: {e}")

print()

# Test 5: Verify pipeline_output.json exists
print("5. Testing Pipeline Output File...")
try:
    with open('pipeline_output.json', 'r') as f:
        pipeline_data = json.load(f)
        print(f"   [OK] pipeline_output.json exists")
        print(f"   [OK] Status: {pipeline_data.get('status', 'unknown')}")
        print(f"   [OK] Regional results: {len(pipeline_data.get('regional_results', []))}")

        # Calculate summary from regions
        regions = pipeline_data.get('regional_results', [])
        total_profit = sum(r.get('weekly_profit', 0) for r in regions)
        total_demand = sum(r.get('total_demand', 0) for r in regions)
        satisfied_demand = sum(r.get('satisfied_demand', 0) for r in regions)
        coverage = (satisfied_demand / total_demand * 100) if total_demand > 0 else 0

        print(f"   [OK] Calculated profit: ${total_profit:,.2f}")
        print(f"   [OK] Calculated coverage: {coverage:.2f}%")

except Exception as e:
    print(f"   [FAIL] Error reading pipeline_output.json: {e}")

print()
print("=== Test Complete ===")
print()
print("Dashboard URLs:")
print(f"  Frontend: {FRONTEND_URL}")
print(f"  Backend API: {BASE_URL}/api")
print()
print("Expected Dashboard Values:")
print(f"  - Weekly Profit: $773,704,018")
print(f"  - Coverage: 59.33%")
print(f"  - 5 Regions: Americas ($480M), Asia ($104M), Europe ($65M), Africa ($67M), Middle East ($55M)")
print()
print("To test the 'Use Real Pipeline' feature:")
print("  1. Open the dashboard in browser")
print("  2. Toggle 'Use Real Pipeline' switch")
print("  3. Click 'Start Pipeline'")
print("  4. Watch real-time updates")

# Open browser
try:
    webbrowser.open(FRONTEND_URL)
    print(f"\n[OK] Opening dashboard in browser...")
except:
    print(f"\n[WARN] Could not auto-open browser. Please manually open: {FRONTEND_URL}")