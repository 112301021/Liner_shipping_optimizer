"""
Runs the test orchestrator pipeline and automatically opens the live dashboard with real output data.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
import threading
import webbrowser

# Add to path
parent_dir = str(Path(__file__).parent)
sys.path.insert(0, parent_dir)

def start_backend():
    """Start the backend server"""
    print("Starting backend server...")
    backend_path = os.path.join(parent_dir, "backend")
    server_script = os.path.join(backend_path, "server.py")

    # Run backend in background
    import subprocess
    backend_proc = subprocess.Popen(
        [sys.executable, server_script],
        cwd=backend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for backend to start
    time.sleep(3)
    print(f"Backend server started (PID: {backend_proc.pid})")
    return backend_proc

def start_frontend():
    """Start the frontend development server"""
    print("Starting frontend server...")
    frontend_path = os.path.join(parent_dir, "frontend")

    # Run npm dev in background
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    # Wait for frontend to start
    time.sleep(5)
    print(f"Frontend server started (PID: {frontend_proc.pid})")
    return frontend_proc

async def trigger_pipeline():
    """Trigger the actual pipeline execution via WebSocket"""
    import websockets

    # Connect to backend WebSocket
    ws_url = "ws://localhost:8000/ws/pipeline"

    try:
        import asyncio
        import websockets

        async def send_message():
            async with websockets.connect(ws_url) as websocket:
                # Send start pipeline message with real pipeline flag
                message = {
                    "type": "start_pipeline",
                    "config": {
                        "max_iterations": 3,
                        "convergence_threshold": 0.95,
                        "optimization_type": "hybrid"
                    },
                    "data": {
                        "use_real_pipeline": True
                    }
                }
                await websocket.send(json.dumps(message))
                print("Pipeline execution started...")

                # Wait for completion
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"Event: {data.get('type', 'unknown')}")

                    if data.get("type") == "pipeline_completed":
                        print("Pipeline completed successfully!")
                        break
                    elif data.get("type") == "pipeline_error":
                        print(f"Pipeline error: {data.get('error', 'Unknown error')}")
                        break

        await send_message()

    except Exception as e:
        print(f"WebSocket connection failed: {e}")
        print("Opening dashboard anyway...")

def open_dashboard():
    """Open the dashboard in browser"""
    print("Opening dashboard in browser...")

    # Try different ports
    ports = [5173, 5174, 5175, 5176, 5177]

    for port in ports:
        url = f"http://localhost:{port}"
        try:
            webbrowser.open(url)
            print(f"Dashboard opened at {url}")
            break
        except:
            continue

def run_test_orchestrator():
    """Run the test orchestrator and save results"""
    print("\nRunning test orchestrator...")
    print("=" * 70)

    # Import and run test
    from tests.test_orchestrator import test_orchestrator

    # Run the test
    result = test_orchestrator()

    # Save results
    output_file = os.path.join(parent_dir, "latest_test_output.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nTest results saved to {output_file}")

    # Extract key metrics for display
    metrics = result.get("summary_metrics", {})
    regional_results = result.get("regional_results", [])

    print("\nKEY RESULTS:")
    print(f"  • Weekly Profit: ${metrics.get('weekly_profit', 0):,.0f}")
    print(f"  • Annual Profit: ${metrics.get('annual_profit', 0):,.0f}")
    print(f"  • Coverage: {metrics.get('coverage', 0):.1f}%")
    print(f"  • Services: {metrics.get('total_services', 0)}")
    print(f"  • Iterations: {result.get('iterations_run', 1)}")

    print("\nREGIONAL RESULTS:")
    for r in regional_results:
        print(f"  • {r.get('region', 'Unknown')}: "
              f"${r.get('weekly_profit', 0):,.0f} profit, "
              f"{r.get('coverage_percent', 0):.1f}% coverage")

    return result

def main():
    """Main execution function"""
    print("SHIPPING OPTIMIZER - LIVE DASHBOARD WITH PIPELINE")
    print("=" * 70)

    # Store processes to clean up later
    processes = []

    try:
        # 1. Run test orchestrator first
        result = run_test_orchestrator()

        # 2. Start backend server
        backend_proc = start_backend()
        processes.append(backend_proc)

        # 3. Start frontend server
        frontend_proc = start_frontend()
        processes.append(frontend_proc)

        # 4. Open dashboard
        open_dashboard()

        # 5. Trigger pipeline execution
        print("\nTriggering pipeline execution in dashboard...")
        asyncio.run(trigger_pipeline())

        # 6. Keep running
        print("\n" + "=" * 70)
        print("Dashboard is running with live pipeline data!")
        print("The pipeline output has been integrated with the dashboard.")
        print("You can now see the real optimization results in the UI.")
        print("\nDashboard URL: http://localhost:5173 (or higher ports)")
        print("Press Ctrl+C to stop both servers")
        print("=" * 70)

        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")

    finally:
        # Clean up processes
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"Server stopped")
            except:
                try:
                    proc.kill()
                    print(f"Server force-killed")
                except:
                    pass

if __name__ == "__main__":
    main()