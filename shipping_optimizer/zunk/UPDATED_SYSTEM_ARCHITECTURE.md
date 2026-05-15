# Updated System Architecture
## AI Multi-Agent Liner Shipping Optimization System v2.0
**Date:** 2026-05-09  
**Status:** Production-Ready with Real-time Integration

---

## Architecture Overview

The system has been restructured into a clean, event-driven architecture with proper separation of concerns and real-time streaming capabilities.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend API    │     │  AI Pipeline    │
│   (React)       │◄────►│   (FastAPI)      │◄────►│  (Orchestrator) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ SQLite Database  │
                       │   (Persistence)  │
                       └──────────────────┘
```

---

## Component Architecture

### Frontend Layer
```
maritime_dashboard.jsx (UI - IMMUTABLE)
    ↓
Zustand Store (State Management)
    ↓
WebSocket Client (Real-time Updates)
    ↓
API Client (REST Calls)
```

### Backend Layer
```
FastAPI Server (Unified - Port 8000)
    ├─ WebSocket Endpoint (/ws)
    ├─ REST API Endpoints (/api/*)
    ├─ Event Validator (Schema Validation)
    └─ Database Layer (SQLite)
```

### AI Pipeline Layer
```
OrchestratorAgent
    ├─ NetworkLoader (Data Loading)
    ├─ RegionalAgent (×5)
    ├─ ServiceGenerator
    ├─ FrequencyGA (Genetic Algorithm)
    ├─ HubMILP (MILP Solver)
    └─ CoordinatorAgent
```

---

## Data Flow Architecture

### Real-time Flow
```
1. User clicks "Start Pipeline" in Dashboard
   ↓
2. Frontend sends WebSocket event: {type: "start_pipeline", data: {...}}
   ↓
3. Backend validates event and triggers orchestrator
   ↓
4. Orchestrator streams events via callbacks:
   - stage_started → stage_progress → stage_completed
   - region_updated (per region)
   - iteration_updated (per iteration)
   - map_updated (corridor data)
   ↓
5. Backend broadcasts validated events to all clients
   ↓
6. Frontend Zustand store updates components
   ↓
7. Dashboard re-renders with live data
```

### Persistence Flow
```
Pipeline Events
    ↓
SQLite Database
    ├─ optimization_runs (run metadata)
    ├─ regional_results (per region)
    ├─ iterations (convergence history)
    └─ corridors (map data)
    ↓
REST API (/api/history)
    ↓
Historical Dashboard View
```

---

## WebSocket Architecture

### Connection Management
```python
WebSocketManager
    ├─ Active Connections List
    ├─ Thread-safe Operations (asyncio.Lock)
    ├─ Broadcast to All Clients
    └─ Personal Messages
```

### Event Types
```python
# Client → Server Events
CLIENT_EVENTS = {
    "ping",
    "start_pipeline",
    "stop_pipeline", 
    "get_status"
}

# Server → Client Events  
SERVER_EVENTS = {
    "pipeline_started",
    "pipeline_completed",
    "pipeline_error",
    "stage_started",
    "stage_progress",
    "stage_completed",
    "region_updated",
    "iteration_updated",
    "map_updated",
    "initial_state",
    "status_update",
    "pong"
}
```

### Event Validation
```python
# All events validated with Pydantic models
class PipelineStartedEvent(BaseEvent):
    type: Literal["pipeline_started"] = "pipeline_started"
    data: Dict[str, Any] = Field(...)

# Runtime validation prevents errors
event = EventValidator.validate_incoming(message)
```

---

## Database Schema

### Tables
```sql
-- Optimization runs metadata
CREATE TABLE optimization_runs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    config TEXT,
    metrics TEXT,
    duration REAL
);

-- Regional optimization results
CREATE TABLE regional_results (
    id INTEGER PRIMARY KEY,
    run_id INTEGER,
    region TEXT NOT NULL,
    profit REAL,
    coverage REAL,
    services INTEGER,
    cost REAL
);

-- Iteration history
CREATE TABLE iterations (
    id INTEGER PRIMARY KEY,
    run_id INTEGER,
    iteration INTEGER,
    profit REAL,
    coverage REAL,
    score REAL,
    reason TEXT
);

-- Maritime corridors
CREATE TABLE corridors (
    id INTEGER PRIMARY KEY,
    run_id INTEGER,
    from_port TEXT,
    to_port TEXT,
    teu INTEGER,
    region TEXT
);
```

---

## API Endpoints

### WebSocket
- `ws://localhost:8000/ws` - Main real-time endpoint

### REST API
```
GET  /api/health          - Health check
GET  /api/status          - Current pipeline status
GET  /api/metrics         - Global optimization metrics
GET  /api/regions         - Regional agent results
GET  /api/iterations      - Iteration history
GET  /api/corridors       - Map corridor data
GET  /api/history         - Historical runs (from DB)
POST /api/optimize        - Trigger optimization
DELETE /api/reset          - Reset state
```

---

## Configuration Architecture

### Backend Config
```python
# FastAPI Settings
HOST = "0.0.0.0"
PORT = 8000
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

# Database
DB_PATH = "optimization_results.db"

# WebSocket
WS_ENDPOINT = "/ws"
MAX_CONNECTIONS = 100
```

### Pipeline Config
```python
# Default Optimization Parameters
DEFAULT_CONFIG = {
    "dataset_path": "data/liner_shipping_dataset.csv",
    "max_iterations": 3,
    "coverage_target": 70.0,
    "profit_weight": 0.6,
    "coverage_weight": 0.4
}
```

---

## Security Architecture

### Input Validation
- All WebSocket events validated with Pydantic
- Type safety prevents injection attacks
- Schema mismatch errors logged and handled

### Error Isolation
- Invalid events don't crash server
- WebSocket errors isolated per connection
- Database operations wrapped in try/catch

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Architecture

### Concurrency Model
```python
# Async/Await throughout
async def websocket_endpoint(websocket: WebSocket):
    async with websocket_manager._lock:
        # Thread-safe operations
        
# Non-blocking database operations
async def save_to_database(event_data):
    await asyncio.to_thread(db.execute, ...)
```

### Memory Management
- WebSocket connections tracked and cleaned up
- Database connections properly closed
- Event data minimally cached in memory

### Scalability Features
- Database persistence enables horizontal scaling
- Event-driven architecture supports load balancing
- Stateless WebSocket handlers

---

## Error Handling Architecture

### WebSocket Errors
```python
try:
    event = EventValidator.validate_incoming(message)
except ValueError as e:
    # Send error response, don't crash
    await send_error(websocket, str(e))
```

### Pipeline Errors
```python
try:
    await orchestrator.run_optimization()
except Exception as e:
    # Broadcast error to all clients
    await websocket_manager.broadcast("pipeline_error", {
        "error": str(e),
        "stage": current_stage
    })
```

### Database Errors
```python
try:
    conn = sqlite3.connect(DB_PATH)
    # Database operations
except sqlite3.Error as e:
    logger.error(f"Database error: {e}")
    # Continue without persistence if needed
```

---

## Deployment Architecture

### Development
```
Terminal 1: Backend Server
$ python backend/main.py

Terminal 2: Frontend Dev Server  
$ npm run dev

Terminal 3: Dashboard Launcher
$ start_live_dashboard.bat
```

### Production (Future)
```
Docker Container 1: FastAPI Backend
Docker Container 2: Nginx (Frontend)
Docker Container 3: PostgreSQL (Database)
Load Balancer: API Gateway
```

---

## Monitoring Architecture

### Logging
- Structured logging with timestamps
- WebSocket connection tracking
- Pipeline stage timing
- Error context capture

### Metrics
- WebSocket connection count
- Pipeline execution duration
- Database query performance
- Error rates by event type

### Health Checks
```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(websocket_manager.active_connections),
        "pipeline_status": current_run_state.get("status")
    }
```

---

## Future Enhancements

### Phase 1: Production Hardening
- [ ] Authentication & Authorization
- [ ] Rate limiting on WebSocket
- [ ] Connection limits
- [ ] HTTPS/WSS support

### Phase 2: Performance
- [ ] Redis caching for hot data
- [ ] Database connection pooling
- [ ] Event streaming with Kafka
- [ ] Horizontal pod autoscaling

### Phase 3: Features
- [ ] Multi-user dashboard support
- [ ] Real-time collaboration
- [ ] Advanced what-if analysis
- [ ] ML-based optimization suggestions

---

## Conclusion

The updated architecture provides:
1. **Clean separation** of concerns across layers
2. **Event-driven** real-time communication
3. **Persistent** storage of all optimization data
4. **Scalable** foundation for future enhancements
5. **Robust** error handling and validation

The system is now architecturally sound and ready for production deployment with proper frontend integration.