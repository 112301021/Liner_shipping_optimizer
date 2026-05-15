import asyncio
import websockets
import json
import sys

async def test_pipeline():
    uri = "ws://localhost:8000/ws/pipeline"
    try:
        # Need to provide an allowed origin
        async with websockets.connect(uri, extra_headers={"Origin": "http://localhost:5173"}) as websocket:
            print("Connected to WebSocket.")
            
            # Wait for initial_state
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received initial state type: {data.get('type')}")
            
            # Start pipeline
            await websocket.send(json.dumps({
                "type": "start_pipeline",
                "data": {"dataset_path": "data/datasets/large_shipping_problem.json"}
            }))
            print("Sent start_pipeline message.")
            
            # Listen to a few messages
            for i in range(5):
                msg = await websocket.recv()
                data = json.loads(msg)
                print(f"Event: {data.get('type')} - {data.get('data', {}).get('stage', '')}")
                if data.get('type') == 'pipeline_error':
                    print(f"Pipeline error: {data}")
                    sys.exit(1)
            
            print("Pipeline successfully started and streaming events via WebSocket.")
    except Exception as e:
        print(f"WebSocket test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_pipeline())
