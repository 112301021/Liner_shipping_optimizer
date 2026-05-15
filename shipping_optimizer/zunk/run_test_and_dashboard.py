"""
Run test_orchestrator.py and then open the dashboard with the results
"""

import os
import sys
import time
import subprocess
from pathlib import Path

print("=" * 70)
print("TEST ORCHESTRATOR + DASHBOARD")
print("=" * 70)

# Step 1: Run test orchestrator
print("\n1. Running test_orchestrator.py...")
print("-" * 50)

# Add parent to path
parent_dir = str(Path(__file__).parent)
sys.path.insert(0, parent_dir)

# Import and run test
from tests.test_orchestrator import test_orchestrator

# Run the test
result = test_orchestrator()

print("\n2. Starting backend server...")
print("-" * 50)

# Start backend
backend_path = os.path.join(parent_dir, "backend")
backend_proc = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd=backend_path,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for backend
time.sleep(3)
print("Backend server started!")

# Step 3: Start frontend
print("\n3. Starting frontend server...")
print("-" * 50)

frontend_path = os.path.join(parent_dir, "frontend")
frontend_proc = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=frontend_path,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True
)

# Wait for frontend
time.sleep(5)
print("Frontend server started!")

# Step 4: Open dashboard
print("\n4. Opening dashboard...")
print("-" * 50)

import webbrowser
webbrowser.open("http://localhost:5173")

print("Dashboard opened!")
print("\n" + "=" * 70)
print("INSTRUCTIONS:")
print("1. The dashboard is now open")
print("2. Check 'Use Real Pipeline' box")
print("3. Click 'Start Pipeline'")
print("4. You'll see the actual test results!")
print("=" * 70)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    backend_proc.terminate()
    frontend_proc.terminate()
    print("Done!")