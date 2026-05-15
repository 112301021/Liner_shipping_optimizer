"""
Test script to verify the dashboard loads and displays data
"""
import requests
import json
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_dashboard_backend():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000/api"

    print("Testing Dashboard Backend API...")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

    # Test pipeline data endpoint
    try:
        response = requests.get(f"{base_url}/pipeline/data")
        if response.status_code == 200:
            print("✅ Pipeline data endpoint working")
            data = response.json()
            print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        else:
            print(f"❌ Pipeline data failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Pipeline data error: {e}")
        return False

    # Test pipeline status endpoint
    try:
        response = requests.get(f"{base_url}/pipeline/status")
        if response.status_code == 200:
            print("✅ Pipeline status endpoint working")
            status = response.json()
            print(f"   Status: {status.get('state', {}).get('status', 'Unknown')}")
        else:
            print(f"❌ Pipeline status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Pipeline status error: {e}")
        return False

    return True

def test_frontend_access():
    """Test if frontend is accessible"""
    import subprocess
    import time

    print("\nTesting Frontend Access...")

    # Check if frontend is running on port 3000
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible on http://localhost:3000")
            print("   You can now open the dashboard in your browser!")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not accessible on http://localhost:3000")
        print("   Make sure the Vite dev server is running: cd frontend && npm run dev")
    except Exception as e:
        print(f"❌ Frontend test error: {e}")

    return False

if __name__ == "__main__":
    backend_ok = test_dashboard_backend()
    frontend_ok = test_frontend_access()

    print("\n" + "="*50)
    if backend_ok and frontend_ok:
        print("✅ DASHBOARD IS READY!")
        print("   Open http://localhost:3000 in your browser")
    else:
        print("❌ Issues detected:")
        if not backend_ok:
            print("   - Backend server issues")
        if not frontend_ok:
            print("   - Frontend server issues")
    print("="*50)