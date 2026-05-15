# 🚀 Live Dashboard Integration

This document explains how to run the real-time AI shipping optimization dashboard.

## 📋 Prerequisites

- Node.js 16+ for frontend
- Python 3.8+ for backend
- WebSocket-enabled browser

## 🚀 Quick Start

### 1. Start Backend Server

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
python server.py
```

The backend will start at `http://localhost:8000`

### 2. Start Frontend

Open another terminal and run:

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

### 3. Open Dashboard

Navigate to `http://localhost:5173` in your browser.

## 🔧 Architecture

### Backend (FastAPI)
- **WebSocket Server**: Real-time event streaming
- **REST API**: HTTP endpoints for data fetching
- **State Management**: In-memory storage for pipeline state

### Frontend (React)
- **WebSocket Client**: Live connection to backend
- **Zustand Store**: Centralized state management
- **Custom Hooks**: API and WebSocket integration
- **Live Components**: Real-time UI updates

## 📡 Features

### Real-time Updates
- Pipeline execution progress
- Stage-by-stage visualization
- Regional optimization results
- Live metrics updates

### Interactive Elements
- Start/Stop pipeline controls
- Region selection
- Live status indicators
- Animated transitions

## 🔄 WebSocket Events

The backend sends these events:

```javascript
// Pipeline lifecycle
pipeline_started
stage_started
stage_progress
stage_completed
pipeline_completed
pipeline_error

// Data updates
region_update
metrics_update
iteration_update
map_update
```

## 🎯 Key Components

### Backend Components
- `server.py` - Main FastAPI server
- WebSocket connection manager
- Pipeline simulation logic
- API endpoints

### Frontend Components
- `LiveDashboard.jsx` - Main dashboard
- `LiveKPICards.jsx` - Metrics display
- `LivePipelineGraph.jsx` - Pipeline visualization
- `LiveRegionalCards.jsx` - Regional results
- `useWebSocket.js` - WebSocket hook
- `useApiData.js` - API hooks
- `dashboardStore.js` - State store

## 🛠️ Configuration

### Pipeline Config
```javascript
{
  max_iterations: 3,
  convergence_threshold: 0.95,
  optimization_type: "hybrid"
}
```

### WebSocket Settings
- URL: `ws://localhost:8000/ws/pipeline`
- Auto-reconnect: Enabled (max 5 attempts)
- Reconnect interval: 5 seconds

## 📊 Data Flow

1. User clicks "Start Pipeline"
2. Frontend sends WebSocket message
3. Backend starts simulation
4. Backend streams events in real-time
5. Frontend updates UI components
6. Zustand store maintains state

## 🎨 Visual Features

- Animated stage progress
- Pulsing live indicators
- Smooth metric transitions
- Interactive region cards
- Real-time status badges

## 🔍 Monitoring

### Connection Status
- Green dot: Connected
- Yellow dot: Connecting
- Red dot: Disconnected

### Pipeline Status
- Idle: Ready to run
- Running: Currently executing
- Completed: Finished successfully
- Error: Execution failed

## 🚨 Troubleshooting

### Frontend Not Connecting
1. Check if backend is running at port 8000
2. Verify WebSocket URL in `websocket.js`
3. Check browser console for errors

### Backend Not Starting
1. Check Python version (3.8+)
2. Install requirements: `pip install -r requirements.txt`
3. Check if port 8000 is available

### Updates Not Showing
1. Verify WebSocket connection
2. Check if "isLive" flag is true
3. Refresh browser connection

## 🎯 Next Steps

To integrate with your actual optimization pipeline:

1. Replace simulation in `server.py` with real orchestrator calls
2. Connect to your actual optimization agents
3. Use real data from your pipeline outputs
4. Add authentication if needed
5. Persist state to database

## 💡 Tips

- Keep the WebSocket connection open for best performance
- Use browser dev tools to monitor WebSocket messages
- Check the console for debug information
- The dashboard auto-refreshes every 5 seconds when not live

## 🐛 Known Issues

- Reconnection may fail after network interruption
- Large data updates might cause brief UI freezes
- Map visualization not yet implemented (placeholder)

---

## 📞 Support

For issues or questions:
1. Check browser console
2. Review backend logs
3. Verify WebSocket connection status
4. Check API endpoints with browser/Postman