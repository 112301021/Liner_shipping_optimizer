# Real-Time Maritime Dashboard Integration

## Overview

This document outlines the complete integration architecture for converting the static React dashboard into a dynamic, real-time system connected to the Python optimization pipeline.

## Architecture

### Backend (FastAPI + WebSocket)

The backend provides:
- **WebSocket Server**: Real-time bi-directional communication
- **REST API**: HTTP endpoints for data retrieval and actions
- **Pipeline Streamer**: Live streaming of optimization execution
- **Event System**: Structured event broadcasting to all clients

### Frontend (React + Zustand)

The frontend includes:
- **API Client**: HTTP and WebSocket communication layer
- **State Management**: Zustand store for dashboard state
- **React Hooks**: Custom hooks for API interactions
- **Live Components**: Dynamic components consuming real-time data

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The server will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available on `http://localhost:5173`

### 3. Test Integration

1. Open the dashboard in your browser
2. Click "▶ Play" to start the optimization pipeline
3. Watch real-time updates as the pipeline executes

## WebSocket Event Protocol

### Client → Server Events

```javascript
// Start optimization pipeline
ws.send(JSON.stringify({
  type: "start_pipeline",
  data: {
    dataset: "data/datasets/large_shipping_problem.json",
    max_iterations: 3
  }
}));

// Stop pipeline
ws.send(JSON.stringify({ type: "stop_pipeline" }));

// Ping for health check
ws.send(JSON.stringify({ type: "ping" }));
```

### Server → Client Events

```javascript
// Initial state
{
  type: "initial_state",
  data: {
    status: "idle",
    problem_stats: { ports: 435, lanes: 9622, ... },
    regions: {},
    metrics: null
  }
}

// Pipeline started
{
  type: "pipeline_started",
  data: {
    status: "running",
    start_time: "2026-05-08T12:00:00Z",
    config: { max_iterations: 3 }
  }
}

// Stage progress
{
  type: "stage_progress",
  data: {
    stage: "decomposition",
    iteration: 0,
    message: "Decomposing problem into regional clusters...",
    progress: 25
  }
}

// Region started
{
  type: "region_started",
  data: {
    region_id: "asia",
    timestamp: "2026-05-08T12:01:00Z"
  }
}

// Iteration complete
{
  type: "iteration_complete",
  data: {
    iteration: 0,
    results: {
      weekly_profit: 740786392,
      coverage: 64.7,
      regions: [...]
    },
    convergence_score: 0.975,
    needs_rerun: true
  }
}

// Map update
{
  type: "map_update",
  data: {
    iteration: 1,
    corridors: [...],
    new_routes: [...]
  }
}

// Pipeline complete
{
  type: "pipeline_complete",
  data: {
    final_metrics: {
      weekly_profit: 773616415,
      coverage: 59.5,
      ...
    }
  }
}
```

## API Endpoints

### REST Endpoints

- `GET /api/health` - Health check
- `GET /api/status` - Current pipeline status
- `GET /api/problem-stats` - Problem statistics
- `GET /api/regions` - Regional agent results
- `GET /api/metrics` - Global optimization metrics
- `GET /api/iterations` - Iteration history
- `GET /api/corridors` - Maritime corridors
- `GET /api/export` - Export full results
- `POST /api/optimize` - Trigger optimization

### WebSocket Endpoint

- `WS /ws` - Real-time event streaming

## Frontend Store Structure

```typescript
interface DashboardStore {
  // Pipeline state
  pipelineStatus: 'idle' | 'running' | 'complete' | 'error' | 'stopped';
  currentIteration: number;
  totalIterations: number;
  progress: number;
  error: string | null;

  // Problem data
  problemStats: ProblemStats | null;

  // Regional data
  regions: Record<string, RegionData>;

  // Global metrics
  metrics: GlobalMetrics | null;

  // Iteration history
  iterations: IterationData[];

  // Map data
  corridors: MapCorridor[];
  activeRoutes: MapCorridor[];

  // Stage progress
  stageProgress: StageProgress | null;

  // Actions for updating state
  setPipelineStatus: (status) => void;
  setMetrics: (metrics) => void;
  addIteration: (iteration) => void;
  // ... other actions
}
```

## Component Integration

### Static → Dynamic Mapping

| Static Component | Dynamic Data Source | Updates |
|----------------|-------------------|---------|
| Hardcoded KPI values | `useMetrics()` | Real-time via WebSocket |
| Fixed region data | `useRegions()` | Live optimization results |
| Static corridors | `useCorridors()` | Dynamic route updates |
| Fixed iterations | `useIterations()` | Feedback loop progress |
| Mock pipeline stages | `useStageProgress()` | Live stage execution |

### Key Components

1. **DashboardProvider**: Integrates WebSocket with store
2. **LiveDashboard**: Main dashboard with real-time data
3. **LiveMapView**: Animated vessel routes
4. **LivePipelineView**: Pipeline execution visualization

## Data Flow

```
Python Pipeline → FastAPI Backend → WebSocket → React Store → UI Components
     ↑                                                                              ↓
     └─────────────────── API Polling (for initial state) ←──────────────────┘
```

## Production Considerations

### Backend
- Use environment variables for configuration
- Implement authentication/authorization
- Add rate limiting
- Set up CORS properly
- Handle reconnection logic

### Frontend
- Error boundaries for graceful failures
- Loading states during data fetching
- Connection status indicators
- Offline mode support
- Performance optimization for large datasets

### Deployment
- Backend: Docker container with gunicorn + uvicorn
- Frontend: Static files served by nginx or CDN
- WebSocket: Ensure proxy support (wss://)
- Scaling: Consider Redis for state sharing

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check backend is running on port 8000
   - Verify CORS settings
   - Check firewall/proxy settings

2. **No Real-Time Updates**
   - Ensure WebSocket is connected
   - Check console for errors
   - Verify event listeners are registered

3. **State Not Updating**
   - Check store subscriptions
   - Verify event handlers
   - Check for race conditions

4. **Performance Issues**
   - Optimize re-renders with React.memo
   - Debounce rapid updates
   - Use pagination for large datasets

## Next Steps

1. **Integrate with Actual Pipeline**
   - Replace mock data with real orchestrator calls
   - Add proper error handling
   - Implement progress tracking

2. **Add Features**
   - Historical data viewing
   - Configuration management
   - Export functionality
   - Alert system

3. **Enhance UI**
   - Add loading animations
   - Improve error display
   - Add tooltips and help
   - Responsive design

4. **Production Readiness**
   - Add monitoring and logging
   - Implement caching
   - Add health checks
   - Set up CI/CD