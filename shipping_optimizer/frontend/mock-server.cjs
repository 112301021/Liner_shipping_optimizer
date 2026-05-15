const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

// Load pipeline data
const pipelineData = JSON.parse(fs.readFileSync(path.join(__dirname, '../pipeline_output.json'), 'utf8'));

// Create WebSocket server
const wss = new WebSocket.Server({ port: 8000 });

console.log('Mock WebSocket server started on port 8000');

wss.on('connection', (ws) => {
  console.log('Client connected');

  // Send initial state
  const initialState = {
    type: 'initial_state',
    data: {
      status: pipelineData.status,
      orchestrator: pipelineData.orchestrator,
      problem_stats: {
        ports: 435,
        lanes: 9622,
        services: 1200,
        weekly_demand: 833484
      },
      metrics: {
        weeklyProfit: pipelineData.regional_results.reduce((sum, r) => sum + r.weekly_profit, 0),
        annualProfit: pipelineData.regional_results.reduce((sum, r) => sum + r.annual_profit, 0),
        coveragePercentage: pipelineData.regional_results.reduce((sum, r) => sum + r.coverage_percent, 0) / pipelineData.regional_results.length,
        totalServices: pipelineData.regional_results.reduce((sum, r) => sum + r.services_selected, 0),
        operatingCost: pipelineData.regional_results.reduce((sum, r) => sum + r.operating_cost, 0),
        convergenceScore: 0.947,
        iterations: [1, 2, 3, 4, 5]
      },
      regions: pipelineData.regional_results.map(r => ({
        name: r.region,
        services: r.services_selected,
        profit: r.weekly_profit,
        demand: r.satisfied_demand,
        coverage: r.coverage_percent
      }))
    }
  };

  ws.send(JSON.stringify(initialState));

  // Simulate live updates
  let updateCount = 0;
  const updateInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      const update = {
        type: 'pipeline_update',
        data: {
          stage: ['Data Loading', 'Regional Selection', 'Service Generation', 'Vessel Assignment', 'Profit Optimization'][updateCount % 5],
          progress: ((updateCount % 5) + 1) * 20,
          iteration: Math.floor(updateCount / 5) + 1,
          metrics: {
            ...initialState.data.metrics,
            weeklyProfit: initialState.data.metrics.weeklyProfit + (Math.random() - 0.5) * 10000,
            convergenceScore: 0.947 + (Math.random() - 0.5) * 0.01
          }
        }
      };
      ws.send(JSON.stringify(update));
      updateCount++;
    } else {
      clearInterval(updateInterval);
    }
  }, 2000);

  ws.on('close', () => {
    console.log('Client disconnected');
    clearInterval(updateInterval);
  });

  ws.on('message', (message) => {
    const parsed = JSON.parse(message);
    console.log('Received:', parsed);

    // Handle ping/pong
    if (parsed.type === 'ping') {
      ws.send(JSON.stringify({ type: 'pong' }));
    }
  });
});

wss.on('error', (error) => {
  console.error('WebSocket server error:', error);
});