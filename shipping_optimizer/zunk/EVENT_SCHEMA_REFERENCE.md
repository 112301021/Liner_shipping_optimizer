# Event Schema Reference
## WebSocket Communication Protocol
**Version:** 2.0  
**Date:** 2026-05-09

---

## Overview

All WebSocket communication follows a strict event-based protocol with validated schemas. Each event has a `type`, `timestamp`, and `data` payload.

### Base Event Structure
```json
{
  "type": "event_type",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": { /* event-specific payload */ }
}
```

---

## Client → Server Events

### 1. start_pipeline
Initiates the optimization pipeline.

```json
{
  "type": "start_pipeline",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {
    "dataset_path": "data/liner_shipping_dataset.csv",
    "max_iterations": 3,
    "config": {
      "coverage_target": 70.0,
      "profit_weight": 0.6,
      "coverage_weight": 0.4
    }
  }
}
```

### 2. stop_pipeline
Stops a running pipeline.

```json
{
  "type": "stop_pipeline",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {}
}
```

### 3. get_status
Requests current pipeline status.

```json
{
  "type": "get_status",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {}
}
```

### 4. ping
Heartbeat to keep connection alive.

```json
{
  "type": "ping",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {}
}
```

---

## Server → Client Events

### Pipeline Events

#### 1. pipeline_started
Pipeline execution has begun.

```json
{
  "type": "pipeline_started",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {
    "run_id": 1,
    "config": {
      "dataset_path": "data/liner_shipping_dataset.csv",
      "max_iterations": 3
    }
  }
}
```

#### 2. pipeline_completed
Pipeline finished successfully.

```json
{
  "type": "pipeline_completed",
  "timestamp": "2026-05-09T10:05:00.000Z",
  "data": {
    "run_id": 1,
    "duration": 300.5,
    "results": {
      "weekly_profit": 773616415,
      "annual_profit": 40228053557,
      "coverage": 59.5,
      "total_services": 465,
      "margin": 84.0,
      "operating_cost": 146921209
    },
    "iterations": [...]
  }
}
```

#### 3. pipeline_error
Pipeline failed with an error.

```json
{
  "type": "pipeline_error",
  "timestamp": "2026-05-09T10:02:00.000Z",
  "data": {
    "error": "Dataset not found: data/liner_shipping_dataset.csv",
    "context": {
      "stage": "loading",
      "operation": "load_problem"
    }
  }
}
```

#### 4. pipeline_stopped
Pipeline was stopped by user.

```json
{
  "type": "pipeline_stopped",
  "timestamp": "2026-05-09T10:03:00.000Z",
  "data": {
    "reason": "User requested stop",
    "partial_results": {
      "completed_stages": 2,
      "total_stages": 5
    }
  }
}
```

### Stage Events

#### 5. stage_started
A pipeline stage has started.

```json
{
  "type": "stage_started",
  "timestamp": "2026-05-09T10:01:00.000Z",
  "data": {
    "stage": "Problem Decomposition",
    "stage_id": "decomposition",
    "stage_index": 0,
    "total_stages": 5,
    "metadata": {
      "regions": ["Asia", "Europe", "Americas", "Middle East", "Africa"],
      "clustering_method": "geographic"
    }
  }
}
```

#### 6. stage_progress
Stage progress update.

```json
{
  "type": "stage_progress",
  "timestamp": "2026-05-09T10:01:30.000Z",
  "data": {
    "stage": "Regional Agents",
    "stage_id": "regional",
    "progress": 50,
    "message": "Processing region 3 of 5"
  }
}
```

#### 7. stage_completed
Stage finished successfully.

```json
{
  "type": "stage_completed",
  "timestamp": "2026-05-09T10:02:00.000Z",
  "data": {
    "stage": "Regional Agents",
    "stage_id": "regional",
    "duration": 60.0,
    "results": {
      "regions_processed": 5,
      "total_profit": 500000000
    }
  }
}
```

### Region Events

#### 8. region_updated
Regional agent completed processing.

```json
{
  "type": "region_updated",
  "timestamp": "2026-05-09T10:01:45.000Z",
  "data": {
    "region_id": "asia",
    "region_data": {
      "name": "Asia",
      "profit": 106904049,
      "coverage": 76.9,
      "services": 99,
      "margin": 79.7,
      "cost": 20610000,
      "uncovered": 24978,
      "hubs": [146, 176, 282, 48, 102],
      "strategy": "hybrid",
      "generated": 802,
      "filtered": 400,
      "selected": 99
    }
  }
}
```

### Iteration Events

#### 9. iteration_started
New optimization iteration.

```json
{
  "type": "iteration_started",
  "timestamp": "2026-05-09T10:01:00.000Z",
  "data": {
    "iteration": 0,
    "max_iterations": 3,
    "message": "Starting optimization iteration 1"
  }
}
```

#### 10. iteration_updated
Iteration results available.

```json
{
  "type": "iteration_updated",
  "timestamp": "2026-05-09T10:02:00.000Z",
  "data": {
    "iteration": 0,
    "iteration_data": {
      "profit": 740786392,
      "coverage": 64.7,
      "score": 0.975,
      "rerun": true,
      "reason": "coverage 64.7% is 5.3pp below 70.0% target",
      "total_services": 450,
      "operating_cost": 142000000,
      "margin": 83.9,
      "regions": [...]
    }
  }
}
```

#### 11. iteration_completed
Iteration fully processed.

```json
{
  "type": "iteration_completed",
  "timestamp": "2026-05-09T10:02:00.000Z",
  "data": {
    "iteration": 0,
    "results": {
      "profit": 740786392,
      "coverage": 64.7
    },
    "convergence_score": 0.975,
    "needs_rerun": true,
    "rerun_reason": "Coverage below target"
  }
}
```

### Map Events

#### 12. map_updated
Maritime map visualization data.

```json
{
  "type": "map_updated",
  "timestamp": "2026-05-09T10:03:00.000Z",
  "data": {
    "corridors": [
      {
        "from": "Port 285",
        "to": "Port 146",
        "teu": 10902,
        "region": "americas"
      },
      {
        "from": "Port 235",
        "to": "Port 36",
        "teu": 5292,
        "region": "americas"
      },
      {
        "from": "Port 221",
        "to": "Port 100",
        "teu": 1932,
        "region": "europe"
      },
      {
        "from": "Port 112",
        "to": "Port 176",
        "teu": 1128,
        "region": "africa"
      }
    ],
    "new_routes": [
      {
        "from": "Port 285",
        "to": "Port 146",
        "teu": 10902,
        "region": "americas"
      }
    ]
  }
}
```

### State Events

#### 13. initial_state
Initial state sent to new clients.

```json
{
  "type": "initial_state",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {
    "status": "idle",
    "run_id": null,
    "current_iteration": 0,
    "current_stage": null,
    "metrics": {},
    "regions": {},
    "iterations": [],
    "corridors": []
  }
}
```

#### 14. state_reset
System state reset.

```json
{
  "type": "state_reset",
  "timestamp": "2026-05-09T10:05:00.000Z",
  "data": {
    "status": "idle",
    "message": "State reset by admin"
  }
}
```

#### 15. status_update
Current status response.

```json
{
  "type": "status_update",
  "timestamp": "2026-05-09T10:02:00.000Z",
  "data": {
    "status": "running",
    "run_id": 1,
    "current_stage": "Regional Agents",
    "current_iteration": 1,
    "start_time": "2026-05-09T10:00:00.000Z",
    "metrics": {
      "weekly_profit": 771721477,
      "coverage": 66.0
    }
  }
}
```

#### 16. pong
Response to ping heartbeat.

```json
{
  "type": "pong",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {}
}
```

---

## Event Validation Rules

### Required Fields
- `type`: Must match one of the defined event types
- `timestamp`: ISO 8601 format (auto-generated by server)
- `data`: Varies by event type, validated against schemas

### Validation Errors
```json
{
  "type": "pipeline_error",
  "timestamp": "2026-05-09T10:00:00.000Z",
  "data": {
    "error": "Event validation failed: Unknown event type",
    "context": {
      "event_type": "invalid_event"
    }
  }
}
```

---

## Event Ordering

### Typical Pipeline Flow
```
1. client: start_pipeline
2. server: pipeline_started
3. server: stage_started (×5)
4. server: stage_progress (×N)
5. server: stage_completed (×5)
6. server: iteration_started (×3)
7. server: region_updated (×5 per iteration)
8. server: iteration_updated (×3)
9. server: map_updated (×1)
10. server: pipeline_completed
```

### Error Recovery
- Any event can be followed by `pipeline_error`
- Client can send `stop_pipeline` at any time
- Server sends `state_reset` after critical errors

---

## Implementation Notes

### Client Side
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Handle events
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case 'pipeline_started':
      // Update UI
      break;
    case 'region_updated':
      // Update region cards
      break;
    // ... handle other events
  }
};

// Start pipeline
ws.send(JSON.stringify({
  type: 'start_pipeline',
  data: {
    dataset_path: 'data/liner_shipping_dataset.csv',
    max_iterations: 3
  }
}));
```

### Server Side
```python
# Send validated event
await websocket_manager.broadcast("region_updated", {
  "region_id": "asia",
  "region_data": {...}
})

# Validate incoming event
event = EventValidator.validate_incoming(message)
if event.type == "start_pipeline":
    await run_optimization(event.data)
```

---

## Version History

### v2.0 (Current)
- Standardized all event names
- Added Pydantic validation
- Separated client/server events
- Added comprehensive metadata

### v1.0 (Legacy)
- Inconsistent event names
- No validation
- Mixed client/server events
- Limited metadata