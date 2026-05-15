#!/usr/bin/env python3
"""
Simple WebSocket Test Client
Tests WebSocket connection and events from the backend
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime

async def test_websocket():
    """Test WebSocket connection and events"""
    uri = "ws://localhost:8000/ws"

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")

            # Send ping
            print("\n📤 Sending ping...")
            await websocket.send(json.dumps({"type": "ping", "data": {}}))

            # Listen for messages
            print("\n📡 Listening for events (press Ctrl+C to stop)...")
            print("-" * 60)

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(message)

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 📨 {data['type']}")

                    # Print key data for important events
                    if data['type'] == 'pipeline_started':
                        print(f"    Run ID: {data['data'].get('run_id')}")
                    elif data['type'] == 'region_updated':
                        print(f"    Region: {data['data']['region_data'].get('name')}")
                    elif data['type'] == 'pipeline_completed':
                        print(f"    Duration: {data['data'].get('duration', 0):.1f}s")

                except asyncio.TimeoutError:
                    print("\n⏰ No events for 30 seconds. Send 'start' to begin pipeline.")

                    # Check for user input
                    print("\nAvailable commands:")
                    print("  start    - Start optimization pipeline")
                    print("  stop     - Stop pipeline")
                    print("  status   - Get current status")
                    print("  quit     - Exit client")

                    cmd = input("\n> ").strip().lower()

                    if cmd == 'start':
                        await websocket.send(json.dumps({
                            "type": "start_pipeline",
                            "data": {
                                "dataset_path": "data/liner_shipping_dataset.csv",
                                "max_iterations": 3
                            }
                        }))
                        print("\n📤 Pipeline start request sent")
                    elif cmd == 'stop':
                        await websocket.send(json.dumps({
                            "type": "stop_pipeline",
                            "data": {}
                        }))
                        print("\n📤 Stop request sent")
                    elif cmd == 'status':
                        await websocket.send(json.dumps({
                            "type": "get_status",
                            "data": {}
                        }))
                        print("\n📤 Status request sent")
                    elif cmd == 'quit':
                        break
                    else:
                        print("\n❓ Unknown command")

    except websockets.exceptions.ConnectionClosed:
        print("\n❌ Connection closed")
    except websockets.exceptions.ConnectionRefused:
        print("\n❌ Connection refused. Is the backend running?")
        print("   Run: cd backend && python main.py")
    except KeyboardInterrupt:
        print("\n\n👋 Disconnecting...")

if __name__ == "__main__":
    print("WebSocket Test Client")
    print("=" * 40)

    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        pass