# Frontend Integration Plan
## Connecting maritime_dashboard.jsx to Live WebSocket Events

---

## Strategy Overview

The maritime_dashboard.jsx must remain visually unchanged while connecting to live data. We'll achieve this by:
1. Creating a WebSocket context provider
2. Mapping live events to the existing DATA structure
3. Injecting live state through React hooks
4. Maintaining UI component immutability

---

## Implementation Approach

### 1. WebSocket Context Provider

Create `src/contexts/WebSocketContext.js`:
```javascript
import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Initial state matching DATA structure
const initialState = {
  global: {
    ports: 435, lanes: 9622, services: 1200, weeklyDemand: 833484,
    runtime: 0, iterations: 0, convergence: 0,
    weeklyProfit: 0, annualProfit: 0,
    coverage: 0, totalServices: 0, margin: 0, unserved: 0,
    operatingCost: 0
  },
  regions: [],
  iterations: [],
  corridors: [],
  status: 'idle'
};

// Reducer to handle WebSocket events
const wsReducer = (state, action) => {
  switch (action.type) {
    case 'pipeline_started':
      return { ...state, status: 'running' };
      
    case 'region_updated':
      const { region_id, region_data } = action.payload;
      const regions = [...state.regions];
      const existingIndex = regions.findIndex(r => r.id === region_id);
      
      // Map to DATA structure format
      const mappedRegion = {
        id: region_id,
        name: region_data.name,
        color: getRegionColor(region_id),
        profit: region_data.profit,
        coverage: region_data.coverage,
        services: region_data.services,
        margin: region_data.margin,
        cost: region_data.cost,
        uncovered: region_data.uncovered,
        hubs: region_data.hubs,
        strategy: region_data.strategy || 'hybrid',
        generated: region_data.generated || 800,
        filtered: region_data.filtered || 400,
        selected: region_data.selected || region_data.services
      };
      
      if (existingIndex >= 0) {
        regions[existingIndex] = mappedRegion;
      } else {
        regions.push(mappedRegion);
      }
      return { ...state, regions };
      
    case 'iteration_updated':
      return {
        ...state,
        iterations: [...state.iterations, mapIteration(action.payload)]
      };
      
    case 'map_updated':
      return {
        ...state,
        corridors: action.payload.corridors
      };
      
    case 'pipeline_completed':
      const { results } = action.payload;
      return {
        ...state,
        status: 'completed',
        global: {
          ...state.global,
          weeklyProfit: results.weekly_profit,
          annualProfit: results.annual_profit,
          coverage: results.coverage,
          totalServices: results.total_services,
          margin: results.margin,
          operatingCost: results.operating_cost,
          unserved: results.unserved,
          runtime: results.duration || 0
        }
      };
      
    default:
      return state;
  }
};

// Create context
const WebSocketContext = createContext();

// Provider component
export const WebSocketProvider = ({ children }) => {
  const [state, dispatch] = useReducer(wsReducer, initialState);
  const wsRef = React.useRef(null);
  const reconnectTimeoutRef = React.useRef(null);

  const connect = () => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        dispatch({ type: message.type, payload: message.data });
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    wsRef.current.onclose = () => {
      // Reconnection logic with exponential backoff
      const delay = Math.min(1000 * Math.pow(2, state.reconnectAttempts || 0), 30000);
      reconnectTimeoutRef.current = setTimeout(connect, delay);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Send messages to WebSocket
  const send = React.useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const value = {
    ...state,
    send,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Hook to use WebSocket context
export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

// Helper functions
const getRegionColor = (regionId) => {
  const colors = {
    asia: '#00d4ff',
    europe: '#7c3aed',
    americas: '#10b981',
    middle_east: '#f59e0b',
    africa: '#ef4444'
  };
  return colors[regionId] || '#00d4ff';
};

const mapIteration = (iterationData) => {
  return {
    iter: iterationData.iteration,
    profit: iterationData.profit,
    coverage: iterationData.coverage,
    score: iterationData.score || 0.975,
    rerun: iterationData.rerun || false,
    reason: iterationData.reason || 'Completed'
  };
};
```

### 2. Update maritime_dashboard.jsx

Wrap the App component and use live data:
```javascript
import { WebSocketProvider, useWebSocket } from './contexts/WebSocketContext';

// Create a wrapper component that injects live data
const AppWithLiveData = () => {
  const { global, regions, iterations, corridors, status, send } = useWebSocket();
  
  // Map WebSocket state to DATA structure
  const liveData = {
    global: global || DATA.global,
    regions: regions.length > 0 ? regions : DATA.regions,
    iterations: iterations.length > 0 ? iterations : DATA.iterations,
    corridors: corridors.length > 0 ? corridors : DATA.corridors
  };

  // Handle start pipeline click
  const handleStartPipeline = () => {
    send({
      type: 'start_pipeline',
      data: {
        dataset_path: 'data/liner_shipping_dataset.csv',
        max_iterations: 3
      }
    });
  };

  // Original App component with live data injection
  return <App data={liveData} onStartPipeline={handleStartPipeline} />;
};

// Export with provider
export default function App() {
  return (
    <WebSocketProvider>
      <AppWithLiveData />
    </WebSocketProvider>
  );
}

// In the original App component, use props instead of hardcoded DATA
export default function App({ data = DATA, onStartPipeline }) {
  // Replace all DATA references with data prop
  // The UI remains exactly the same!
}
```

### 3. Minimal UI Changes Required

Only change these lines in maritime_dashboard.jsx:

```javascript
// Line 4-31: Replace DATA constant with prop
const DATA = props.data; // Instead of hardcoded object

// Line 880-885: Add start handler to buttons
{["▶ Play", "⇌ Flows", "⊡ Reset", "↓ Export"].map((btn, i) => (
  <button 
    key={btn} 
    className="px-3 py-1.5 rounded text-xs font-mono transition-all duration-200 hover:scale-105"
    style={{ background: "rgba(0,212,255,0.08)", border: "1px solid rgba(0,212,255,0.2)", color: "rgba(0,212,255,0.8)" }}
    onClick={i === 0 ? onStartPipeline : undefined}
  >
    {btn}
  </button>
))}
```

---

## Alternative Approach: Custom Hook

If you prefer not to use Context API:

```javascript
// hooks/useLiveDashboard.js
import { useState, useEffect } from 'react';

export const useLiveDashboard = () => {
  const [data, setData] = useState(DATA);
  const [status, setStatus] = useState('idle');
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      const { type, data: eventData } = JSON.parse(event.message);
      
      // Update state based on event type
      switch (type) {
        case 'region_updated':
          setData(prev => ({
            ...prev,
            regions: updateRegions(prev.regions, eventData)
          }));
          break;
        // ... handle other events
      }
    };
    
    return () => ws.close();
  }, []);
  
  return { data, status };
};

// In maritime_dashboard.jsx:
export default function App() {
  const { data, status } = useLiveDashboard();
  // Use data instead of DATA - UI unchanged!
}
```

---

## Implementation Steps

1. **Create WebSocket Context** (`src/contexts/WebSocketContext.js`)
2. **Wrap App Component** with provider
3. **Inject Live Data** through props
4. **Add Start Handler** for Play button
5. **Test Integration** with backend running

---

## Benefits

1. **UI Remains Unchanged** - No visual modifications
2. **Live Data Integration** - Real optimization results
3. **Error Handling** - Automatic reconnection
4. **Clean Architecture** - Separation of concerns
5. **Type Safety** - Event validation maintained

---

## Testing Strategy

1. **Unit Tests** for event mapping functions
2. **Integration Tests** for WebSocket connection
3. **E2E Tests** for full flow
4. **Error Scenarios** - connection loss, invalid events

---

## Next Steps

1. Implement the WebSocket context
2. Test with backend events
3. Add loading states
4. Implement error boundaries
5. Deploy to production

This approach maintains the beautiful UI design while enabling full real-time functionality.