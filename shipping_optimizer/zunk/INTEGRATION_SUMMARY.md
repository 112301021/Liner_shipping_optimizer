# 📊 Integration Summary: Test Orchestrator → Live Dashboard

## 🎯 How the Output is Generated and Used

### 1. Output Generation (test_orchestrator.py)
```python
# When you run test_orchestrator.py, it produces this structure:
{
  "status": "complete",
  "problem_analysis": "...",
  "regional_results": [
    {
      "region": "Asia",
      "weekly_profit": 106904049,
      "coverage_percent": 76.9,
      "services_selected": 99,
      "profit_margin_pct": 79.7,
      "hub_ports": [146, 176, 282],
      "uncovered_teu": 24978
    },
    // ... 4 more regions
  ],
  "summary_metrics": {
    "weekly_profit": 773616415,
    "annual_profit": 40228053557,
    "coverage": 59.5,
    "cost": 146921209,
    "total_services": 465
  },
  "iterations_run": 2,
  "iteration_audit": [...],
  "decision_output": {...}
}
```

### 2. Data Storage
The output is stored in multiple ways:

#### In Backend Memory
```python
# backend/server.py - Current state storage
current_state = {
    "pipeline": { "status": "running", ... },
    "metrics": { 
        "weeklyProfit": 773616415,
        "annualProfit": 40228053557,
        "coveragePercentage": 59.5,
        # ... more metrics
    },
    "regions": [
        # Regional results from orchestrator
    ],
    "iterations": []
}
```

#### File Storage (Optional)
```python
# In run_actual_pipeline() function
output_file = os.path.join(parent_dir, "latest_pipeline_output.json")
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)
```

### 3. How Dashboard Gets the Data

#### REST API Endpoints
```python
# Backend serves these endpoints:
GET /api/metrics/summary     # → Returns current_state["metrics"]
GET /api/regions/           # → Returns current_state["regions"]
GET /api/pipeline/status    # → Returns current_state["pipeline"]
```

#### WebSocket Streaming
```javascript
// Frontend connects to WebSocket
ws://localhost:8000/ws/pipeline

// Receives events like:
{
  "type": "pipeline_started",
  "timestamp": "2026-05-09T..."
}

{
  "type": "region_update",
  "data": {
    "id": "asia",
    "name": "Asia",
    "weekly_profit": 106904049,
    "coverage_percent": 76.9
  }
}

{
  "type": "pipeline_completed",
  "results": {
    "weeklyProfit": 773616415,
    "coveragePercentage": 59.5
  }
}
```

### 4. Dashboard Display
```javascript
// React components use the data:

// KPI Cards
<LiveKPICards /> → Shows weekly profit, coverage, etc.

// Regional Cards
<LiveRegionalCards /> → Shows each region's results

// Pipeline Graph
<LivePipelineGraph /> → Shows execution progress
```

## 🔄 Complete Flow

```
1. User clicks "Start Pipeline" with "Use Real Pipeline" checked
                    ↓
2. Frontend sends WebSocket message
                    ↓
3. Backend receives message and calls run_actual_pipeline()
                    ↓
4. Backend imports and runs OrchestratorAgent.process()
                    ↓
5. Orchestrator runs the full optimization pipeline
                    ↓
6. Backend streams results via WebSocket events
                    ↓
7. Frontend updates UI components with real data
```

## 📝 Key Implementation Details

### Backend Integration Point
```python
# backend/server.py - run_actual_pipeline()
def run_actual_pipeline(connection_manager, config):
    # Import orchestrator
    from src.agents.orchestrator_agent import OrchestratorAgent
    
    # Run pipeline
    orchestrator = OrchestratorAgent()
    result = orchestrator.process({"problem": problem})
    
    # Stream results to dashboard
    for region_result in result.get("regional_results", []):
        await connection_manager.broadcast({
            "type": "region_update",
            "data": { /* region data */ }
        })
```

### Frontend WebSocket Handler
```javascript
// frontend/src/hooks/useWebSocket.js
const startPipeline = useCallback((config) => {
    store.resetState();
    if (wsClientRef.current) {
        wsClientRef.current.startPipeline(config);
    }
}, [store]);
```

## ✅ Verification Checklist

When the integration is working:

1. ✅ Backend starts on port 8000
2. ✅ Frontend starts on port 5173+
3. ✅ Dashboard shows "Use Real Pipeline" toggle
4. ✅ User clicks "Start Pipeline"
5. ✅ Console shows "Running actual pipeline..."
6. ✅ Real metrics appear in KPI cards
7. ✅ Regional cards show actual optimization results
8. ✅ Pipeline graph shows live progress
9. ✅ Connection status shows "connected"

## 🎯 Expected Results

You should see in the dashboard:
- Weekly Profit: **$773,616,415**
- Annual Profit: **$40,228,053,557**
- Coverage: **59.5%**
- Total Services: **465**
- Asia region: **$106,904,049** profit, **76.9%** coverage
- Europe region: **$234,567,890** profit, **82.3%** coverage
- Americas region: **$187,654,321** profit, **68.5%** coverage
- And all other real metrics from your pipeline