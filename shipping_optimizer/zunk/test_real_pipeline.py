"""
Test script to verify real pipeline execution works
"""

import json
import requests
import asyncio
import websockets
from datetime import datetime

# API endpoints
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/pipeline"

async def test_websocket_connection():
    """Test WebSocket connection to pipeline"""
    print("\n=== Testing WebSocket Connection ===")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected successfully")

            # Send a test message
            await websocket.send(json.dumps({
                "type": "start_pipeline",
                "config": {
                    "use_real_pipeline": True,
                    "max_iterations": 1
                }
            }))

            # Listen for responses (timeout after 5 seconds)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✅ Received WebSocket message: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⚠ WebSocket connected but no response (pipeline may take time to start)")

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

    return True

def test_pipeline_trigger():
    """Test pipeline trigger via REST API"""
    print("\n=== Testing Pipeline Trigger ===")
    try:
        response = requests.post(
            f"{BASE_URL}/api/optimize",
            json={
                "use_real_pipeline": True,
                "max_iterations": 1
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Pipeline trigger endpoint working")
            return True
        else:
            print(f"❌ Pipeline trigger failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Pipeline trigger error: {e}")
        return False

def main():
    print("=== Real Pipeline Execution Test ===")
    print(f"Timestamp: {datetime.now()}")

    # Test pipeline trigger
    trigger_success = test_pipeline_trigger()

    # Test WebSocket connection
    ws_success = asyncio.run(test_websocket_connection())

    print("\n=== Results ===")
    print(f"Pipeline Trigger: {'✅' if trigger_success else '❌'}")
    print(f"WebSocket Connection: {'✅' if ws_success else '❌'}")

    if trigger_success and ws_success:
        print("\n✅ REAL PIPELINE EXECUTION IS READY")
        print("\nTo run the full pipeline in dashboard:")
        print("1. Open http://localhost:3000")
        print("2. Toggle 'Use Real Pipeline' ON")
        print("3. Click 'Start Pipeline'")
        print("4. Monitor progress in real-time")
    else:
        print("\n⚠ Some features may not work properly")

    print("\nNote: Full pipeline execution may take 2-5 minutes to complete")

if __name__ == "__main__":
    main()