# 📊 Dashboard Integration Guide

## Overview

The live dashboard has been successfully integrated with the `test_orchestrator.py` pipeline. When you run the test, the dashboard will automatically display the real optimization results.

## 🚀 Quick Start

### Method 1: Using the Batch File (Windows)

1. Double-click `start_live_dashboard.bat`
2. Wait for both servers to start
3. The dashboard will open automatically in your browser
4. Click "Start Pipeline" with "Use Real Pipeline" checked

### Method 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Run Pipeline:**
```bash
python test_pipeline_integration.py
```

### Method 3: Run with Integrated Script

```bash
python run_dashboard_with_pipeline.py
```

## 📡 How It Works

### Data Flow
1. **Test Orchestrator** → Generates optimization results
2. **Backend Server** → Streams results via WebSocket
3. **Frontend Dashboard** → Displays live updates

### Key Integration Points

#### Backend (`backend/server.py`)
- Added `run_actual_pipeline()` function
- Connects to real `OrchestratorAgent`
- Streams live data to frontend via WebSocket
- Updates dashboard state with real metrics

#### Frontend
- Added "Use Real Pipeline" toggle
- WebSocket client connects to backend
- Real-time updates of KPIs, regions, and stages
- Displays actual optimization results

## 🎯 Features

### Live Updates
- ✅ Real-time pipeline progress
- ✅ Stage-by-stage execution
- ✅ Regional optimization results
- ✅ Live metric updates
- ✅ Connection status indicator

### Dashboard Components
- **KPI Cards**: Show profit, coverage, services
- **Pipeline Graph**: Visualizes execution stages
- **Regional Cards**: Display per-region results
- **Status Indicators**: Show live connection status

## 🔧 Configuration

### Pipeline Settings
```javascript
{
  max_iterations: 3,
  convergence_threshold: 0.95,
  optimization_type: "hybrid",
  use_real_pipeline: true  // Use actual orchestrator
}
```

### WebSocket Events
```javascript
// Pipeline events
pipeline_started
stage_started
stage_progress
stage_completed
pipeline_completed

// Data events
region_update
metrics_update
```

## 📊 Test Results

When you run `test_orchestrator.py`, you'll see:
- Actual optimization metrics
- Real regional results
- Live iteration updates
- Real profit and coverage data

## 🐛 Troubleshooting

### Dashboard shows blank page
1. Check if both servers are running
2. Verify browser console for errors
3. Make sure WebSocket connection is established

### No real data showing
1. Check "Use Real Pipeline" toggle
2. Verify backend logs for errors
3. Ensure `test_orchestrator.py` runs successfully

### WebSocket connection failed
1. Backend must be running on port 8000
2. Check firewall settings
3. Try refreshing the browser

## 📝 Architecture Summary

```
test_orchestrator.py
        ↓
OrchestratorAgent
        ↓
Backend (FastAPI + WebSocket)
        ↓
Frontend (React + WebSocket)
        ↓
Live Dashboard UI
```

## 🔄 Next Steps

To use with your own pipeline:
1. Replace the test data in `run_actual_pipeline()`
2. Connect to your actual optimization agents
3. Add custom WebSocket events for your data
4. Customize dashboard components as needed

## 📁 Key Files

- `backend/server.py` - WebSocket server with pipeline integration
- `frontend/src/components/live/` - Live dashboard components
- `test_orchestrator.py` - Pipeline test runner
- `run_dashboard_with_pipeline.py` - Integrated runner script

## 🎉 Success!

The dashboard now successfully integrates with your actual optimization pipeline and displays real-time results as they're generated.