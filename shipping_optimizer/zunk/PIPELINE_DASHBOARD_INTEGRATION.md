# 📊 Pipeline-Dashboard Integration

## How It Works

### 1. Test Orchestrator Output Storage
When `test_orchestrator.py` runs, it now saves output to:
```
pipeline_output.json
```

The JSON contains:
- `summary_metrics` - Global KPIs (profit, coverage, etc.)
- `regional_results` - Data for each region
- `iteration_audit` - Iteration history
- `problem_analysis` - LLM analysis
- `executive_summary` - Final summary

### 2. Backend Loading
The backend server (`server.py`) loads this JSON on startup:
```python
def load_pipeline_data():
    with open("pipeline_output.json", 'r') as f:
        result = json.load(f)
    
    # Update current_state with real data
    current_state["metrics"] = {
        "weeklyProfit": result["summary_metrics"]["weekly_profit"],
        "coveragePercentage": result["summary_metrics"]["coverage"],
        # ... other metrics
    }
```

### 3. Dashboard Display
When user clicks "Start Pipeline" with "Use Real Pipeline":
1. Backend reads the JSON file
2. Streams data via WebSocket
3. Dashboard shows actual optimization results

## Key Changes Made

### 1. test_orchestrator.py
Added JSON output saving:
```python
# Save result to JSON file for dashboard
output_file = Path(__file__).parent.parent / "pipeline_output.json"
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)
```

### 2. backend/server.py
Modified to:
- Load JSON on startup
- Use JSON data instead of running pipeline
- Stream JSON data via WebSocket

### 3. run_test_and_dashboard.py
Created script to:
1. Run test orchestrator
2. Start backend server
3. Start frontend
4. Open dashboard

## Expected Results

When test_orchestrator.py completes, `pipeline_output.json` contains:

```json
{
  "status": "complete",
  "summary_metrics": {
    "weekly_profit": 773616415,
    "annual_profit": 40228053557,
    "coverage": 59.5,
    "total_services": 465
  },
  "regional_results": [
    {
      "region": "Asia",
      "weekly_profit": 106904049,
      "coverage_percent": 76.9,
      "services_selected": 99
    },
    // ... other regions
  ]
}
```

## How to Use

1. Run test orchestrator:
   ```bash
   python tests/test_orchestrator.py
   ```

2. Start servers:
   ```bash
   # Terminal 1
   cd backend && python server.py
   
   # Terminal 2
   cd frontend && npm run dev
   ```

3. Open dashboard:
   - Go to http://localhost:5173
   - Check "Use Real Pipeline"
   - Click "Start Pipeline"
   - See actual test results!

## Data Flow

```
test_orchestrator.py
        ↓ (saves to JSON)
pipeline_output.json
        ↓ (loaded by backend)
backend/server.py
        ↓ (streams via WebSocket)
frontend/dashboard
```

This ensures the dashboard always uses the latest test output from test_orchestrator.py!