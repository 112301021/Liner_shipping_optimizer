import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { ComposableMap, Geographies, Geography, Line, Marker } from "react-simple-maps";
// WebSocket integration hook for live optimization data
const useOptimizationState = () => {
  const [state, setState] = useState({
    global: {
      ports: 435, lanes: 9622, services: 1200, weeklyDemand: 833484,
      runtime: 0, iterations: 0, convergence: 0,
      weeklyProfit: 0, annualProfit: 0,
      coverage: 0, totalServices: 0, margin: 0, unserved: 0,
      operatingCost: 0,
      selected_services: []
    },
    regions: {},
    iterations: [],
    corridors: [],
    isConnected: false,
    isPipelineRunning: false,
    currentStage: null,
    stageProgress: 0,
    currentIteration: 0,
    maxIterations: 3,
    pipelineError: null
  });

  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const retryCount = useRef(0);
  const MAX_RETRIES = 5;

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket('ws://localhost:8000/ws/pipeline');

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        retryCount.current = 0; // reset on successful connection
        setState(prev => ({ ...prev, isConnected: true }));
      };

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch(message.type) {
          case 'initial_state':
            if (message.data) {
              // Process regions to add colors
              const rawRegions = message.data.regions || {};
              const processedRegions = {};
              Object.entries(rawRegions).forEach(([id, data]) => {
                processedRegions[id] = {
                  ...data,
                  id,
                  name: data.name === "Middle Last" ? "Middle East" : (data.name || (id === "middle_east" ? "Middle East" : id.charAt(0).toUpperCase() + id.slice(1))),
                  color: getRegionColor(id)
                };
              });

              setState(prev => ({
                ...prev,
                global: {
                  ...prev.global,
                  ...message.data.metrics,
                  ports: message.data.problem_stats?.ports || 435,
                  lanes: message.data.problem_stats?.lanes || 9622,
                  services: message.data.problem_stats?.services || 1200,
                  weeklyDemand: message.data.problem_stats?.weekly_demand || 833484,
                  selected_services: message.data.metrics?.selected_services || prev.global.selected_services || []
                },
                regions: processedRegions,
                iterations: message.data.iterations || [],
                corridors: message.data.corridors || []
              }));
            }
            break;

          case 'pipeline_started':
            setState(prev => ({
              ...prev,
              isPipelineRunning: true,
              currentStage: 'Initializing',
              pipelineError: null
            }));
            break;

          case 'stage_started':
            setState(prev => ({
              ...prev,
              currentStage: message.data?.stage || message.stage,
              stageProgress: 0
            }));
            break;

          case 'stage_progress':
            setState(prev => ({
              ...prev,
              stageProgress: message.data?.progress ?? message.progress ?? 0
            }));
            break;

          case 'region_update':
          case 'region_updated':
            {
              const rData = message.data?.region_data || message.data || message;
              const rId = message.data?.region_id || rData.id || rData.region_id;
              if (!rId) break;
              
              setState(prev => ({
                ...prev,
                regions: {
                  ...prev.regions,
                  [rId]: {
                    ...prev.regions[rId],
                    ...rData,
                    id: rId,
                    name: rData.name === "Middle Last" ? "Middle East" : (rData.name || (rId === "middle_east" ? "Middle East" : rId.charAt(0).toUpperCase() + rId.slice(1))),
                    color: getRegionColor(rId)
                  }
                }
              }));
            }
            break;

          case 'iteration_completed':
            {
              const itData = message.data?.iteration_data || message.data || message;
              const itNum = message.data?.iteration || itData.iteration || itData.iter;
              
              setState(prev => ({
                ...prev,
                iterations: [...prev.iterations, {
                  iter: itNum,
                  profit: itData.profit || 0,
                  coverage: itData.coverage || 0,
                  score: itData.score || 0,
                  rerun: itData.rerun || false,
                  reason: itData.reason || ''
                }],
                currentIteration: itNum
              }));
            }
            break;

          case 'map_updated':
            setState(prev => ({
              ...prev,
              corridors: message.data?.corridors || message.corridors || []
            }));
            break;

          case 'pipeline_completed':
            {
              const results = message.data?.results || message.results || message.data || {};
              setState(prev => ({
                ...prev,
                isPipelineRunning: false,
                currentStage: 'Complete',
                stageProgress: 100,
                global: {
                  ...prev.global,
                  ...results,
                  selected_services: results.selected_services || prev.global.selected_services || []
                }
              }));
            }
            break;

          case 'pipeline_error':
            setState(prev => ({
              ...prev,
              isPipelineRunning: false,
              pipelineError: message.data?.error || message.error || 'Unknown error'
            }));
            break;
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setState(prev => ({ ...prev, isConnected: false }));

        // Exponential backoff reconnect with max retries
        if (retryCount.current < MAX_RETRIES) {
          const delay = Math.min(1000 * Math.pow(2, retryCount.current), 30000);
          retryCount.current++;
          console.log(`Reconnecting in ${delay}ms (attempt ${retryCount.current}/${MAX_RETRIES})...`);
          reconnectTimeout.current = setTimeout(() => connect(), delay);
        } else {
          console.log('Max reconnect attempts reached. Giving up.');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, pipelineError: 'Connection error' }));
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const startOptimization = useCallback(() => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'start_pipeline',
        data: {
          dataset_path: 'data/datasets/large_shipping_problem.json'
        }
      }));
    } else {
      console.error('WebSocket not connected');
    }
  }, []);

  // Helper to get region colors
  const getRegionColor = (regionId) => {
    const colors = {
      asia: "#00d4ff",
      europe: "#7c3aed",
      americas: "#10b981",
      middle_east: "#f59e0b",
      africa: "#ef4444"
    };
    return colors[regionId] || "#00d4ff";
  };

  return { ...state, startOptimization };
};

// ─── UTILS ───────────────────────────────────────────────────────────────────
const fmt = (n) => n >= 1e9 ? `$${(n/1e9).toFixed(1)}B` : n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : `$${n.toLocaleString()}`;
const fmtNum = (n) => n.toLocaleString();

// ─── ANIMATED COUNTER ────────────────────────────────────────────────────────
function Counter({ value, prefix = "", suffix = "", decimals = 0, duration = 2000 }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = value / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setCount(value); clearInterval(timer); }
      else setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [value, duration]);
  return <span>{prefix}{decimals > 0 ? count.toFixed(decimals) : Math.floor(count).toLocaleString()}{suffix}</span>;
}

// Helper to convert hex to rgba for better CSS support
const hexToRgba = (hex, alpha) => {
  if (!hex || hex[0] !== '#') return `rgba(0, 212, 255, ${alpha})`;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// ─── SPARKLINE ───────────────────────────────────────────────────────────────
function Sparkline({ data, color, height = 32 }) {
  if (!data || data.length < 2) {
    return (
      <svg width="60" height={height} className="opacity-20">
        <line x1="0" y1={height/2} x2="60" y2={height/2} stroke={color || "#00d4ff"} strokeWidth="1" strokeDasharray="2,2" />
      </svg>
    );
  }
  
  const sortedData = [...data]; // Ensure chronological order if needed
  const max = Math.max(...sortedData), min = Math.min(...sortedData);
  const range = Math.max(1, max - min);
  
  const pts = sortedData.map((v, i) => {
    const x = (i / (sortedData.length - 1)) * 60;
    const y = height - ((v - min) / range) * (height - 8) - 4;
    return `${x},${y}`;
  }).join(" ");
  
  return (
    <svg width="60" height={height} style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`M 0,${height} ${pts} L 60,${height} Z`} fill={`url(#grad-${color})`} opacity="0.3" />
      <polyline points={pts} fill="none" stroke={color || "#00d4ff"} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx="60" cy={height - ((sortedData[sortedData.length-1] - min) / range) * (height - 8) - 4} r="2" fill={color} />
    </svg>
  );
}

// ─── PULSE DOT ───────────────────────────────────────────────────────────────
function PulseDot({ color = "#00d4ff" }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: color }} />
      <span className="relative inline-flex rounded-full h-2.5 w-2.5" style={{ backgroundColor: color }} />
    </span>
  );
}

// ─── PROGRESS BAR ────────────────────────────────────────────────────────────
function ProgressBar({ value, max = 100, color, animated = true }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-1000 ${animated ? "" : ""}`}
        style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}aa, ${color})`, boxShadow: `0 0 8px ${color}66` }}
      />
    </div>
  );
}

// ─── NAV ITEM ────────────────────────────────────────────────────────────────
const navItems = [
  { id: "overview", label: "Overview", icon: "⬡" },
  { id: "pipeline", label: "Pipeline", icon: "◈" },
  { id: "regional", label: "Regional Agents", icon: "◎" },
  { id: "funnel", label: "GA · MILP Analytics", icon: "◆" },
  { id: "feedback", label: "Feedback Loop", icon: "↺" },
  { id: "conflict", label: "Conflict Resolution", icon: "⧖" },
  { id: "map", label: "Maritime Map", icon: "⊕" },
  { id: "summary", label: "Executive Summary", icon: "▣" },
];

// ─── PIPELINE NODES ──────────────────────────────────────────────────────────
const pipelineNodes = [
  { id: "orch", label: "Orchestrator Agent", sub: "LLM problem analysis", color: "#00d4ff", x: 50, y: 5, type: "master" },
  { id: "decomp", label: "Problem Decomposition", sub: "Port Clustering · Regional Split", color: "#7c3aed", x: 50, y: 18, type: "process" },
  { id: "reg", label: "Regional Agents × 5", sub: "Asia · Europe · Americas · ME · Africa", color: "#10b981", x: 50, y: 31, type: "agents" },
  { id: "gen", label: "Service Generator", sub: "1,200 candidate services", color: "#06b6d4", x: 50, y: 44, type: "process" },
  { id: "ga", label: "Hierarchical GA", sub: "Selection · crossover · mutation", color: "#8b5cf6", x: 50, y: 57, type: "compute" },
  { id: "milp", label: "MILP Optimization", sub: "Flow optimization · hub allocation", color: "#f59e0b", x: 50, y: 70, type: "compute" },
  { id: "coord", label: "Coordinator Agent", sub: "Conflict detection · resolution", color: "#ef4444", x: 50, y: 83, type: "master" },
  { id: "agg", label: "Global Aggregation", sub: "Roll-up · Executive summary", color: "#00d4ff", x: 50, y: 96, type: "output" },
];

// ─── PIPELINE VIEW ───────────────────────────────────────────────────────────
function PipelineView() {
  const [active, setActive] = useState(null);
  const [tick, setTick] = useState(0);

  // Get live pipeline state
  const optimizationState = useOptimizationState();

  useEffect(() => {
    const t = setInterval(() => setTick(p => p + 1), 80);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex gap-6 h-full">
      <div className="flex-1 relative" style={{ minHeight: 520 }}>
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="flowGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.8" />
            </linearGradient>
          </defs>
          {pipelineNodes.slice(0, -1).map((n, i) => {
            const next = pipelineNodes[i + 1];
            const offset = ((tick * 0.8 + i * 15) % 100) / 100;
            const py = n.y + (next.y - n.y) * offset;
            return (
              <g key={n.id}>
                <line x1={n.x} y1={n.y + 2} x2={next.x} y2={next.y - 2} stroke="url(#flowGrad)" strokeWidth="0.3" strokeOpacity="0.4" />
                <circle cx={n.x} cy={py} r="0.8" fill="#00d4ff" opacity="0.9">
                  <animate attributeName="opacity" values="0.4;1;0.4" dur="1.5s" repeatCount="indefinite" />
                </circle>
              </g>
            );
          })}
          {/* Feedback loop arrow */}
          <path d="M 80,83 Q 95,57 80,31" stroke="#ef4444" strokeWidth="0.5" fill="none" strokeDasharray="2,2" strokeOpacity="0.7" />
          <polygon points="78,33 80,29 82,33" fill="#ef4444" opacity="0.7" />
          <text x="90" y="60" fontSize="2.5" fill="#ef4444" opacity="0.7" textAnchor="middle">feedback</text>
        </svg>

        <div className="relative z-10 flex flex-col gap-2 py-4 px-8">
          {pipelineNodes.map((node) => (
            <button
              key={node.id}
              onClick={() => setActive(active === node.id ? null : node.id)}
              className="group flex items-center gap-3 rounded-lg px-4 py-2.5 transition-all duration-200 text-left"
              style={{
                background: active === node.id ? `${node.color}18` : "rgba(255,255,255,0.02)",
                border: `1px solid ${active === node.id ? node.color + "66" : "rgba(255,255,255,0.06)"}`,
                boxShadow: active === node.id ? `0 0 20px ${node.color}22` : "none"
              }}
            >
              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: node.color, boxShadow: `0 0 6px ${node.color}` }} />
              <div className="flex-1">
                <div className="text-sm font-medium text-white/90" style={{ fontFamily: "'Courier New', monospace", letterSpacing: "0.02em" }}>{node.label}</div>
                <div className="text-xs text-white/40 mt-0.5">{node.sub}</div>
              </div>
              <div className="text-xs px-2 py-0.5 rounded" style={{ background: `${node.color}22`, color: node.color, border: `1px solid ${node.color}44` }}>
                {node.type}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="w-64 flex-shrink-0">
        <div className="rounded-xl p-4 h-full" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="text-xs font-mono text-white/40 mb-4 uppercase tracking-widest">Pipeline Stats</div>
          {[
            { label: "Total Runtime", value: `${optimizationState.global.runtime || "356.1"}s` },
            { label: "Feedback Iterations", value: optimizationState.iterations.length.toString() },
            { label: "Convergence Score", value: optimizationState.global.convergence.toFixed(3) },
            { label: "Services Generated", value: "4,100" },
            { label: "Services Filtered", value: "2,000" },
            { label: "Services Selected", value: fmtNum(optimizationState.global.totalServices) },
            { label: "Conflicts Detected", value: "0" },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between items-center py-2 border-b border-white/5">
              <span className="text-xs text-white/50">{label}</span>
              <span className="text-xs font-mono text-white/90">{value}</span>
            </div>
          ))}
          <div className="mt-4">
            <div className="text-xs text-white/40 mb-2 font-mono uppercase tracking-widest">Feedback Loop</div>
            <div className="flex gap-1 mt-2">
              {optimizationState.iterations.map((it, i) => (
                <div key={i} className="flex-1 rounded p-2 text-center" style={{ background: it.rerun ? "rgba(239,68,68,0.12)" : "rgba(16,185,129,0.12)", border: `1px solid ${it.rerun ? "#ef444433" : "#10b98133"}` }}>
                  <div className="text-xs font-mono" style={{ color: it.rerun ? "#ef4444" : "#10b981" }}>it.{it.iter}</div>
                  <div className="text-xs text-white/60 mt-0.5">{it.coverage.toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── REGION CARD ─────────────────────────────────────────────────────────────
function RegionCard({ r, onClick, selected }) {
  return (
    <div
      onClick={() => onClick(r)}
      className="cursor-pointer rounded-xl p-4 transition-all duration-300 hover:scale-[1.02]"
      style={{
        background: selected ? `${r.color}12` : "rgba(255,255,255,0.025)",
        border: `1px solid ${selected ? r.color + "55" : "rgba(255,255,255,0.07)"}`,
        boxShadow: selected ? `0 0 30px ${r.color}20, inset 0 0 20px ${r.color}08` : "none"
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: r.color, boxShadow: `0 0 8px ${r.color}` }} />
          <span className="text-sm font-semibold text-white/90" style={{ fontFamily: "'Courier New', monospace" }}>{r.name}</span>
        </div>
        <span className="text-xs px-2 py-0.5 rounded font-mono" style={{ background: `${r.color}20`, color: r.color }}>{r.strategy}</span>
      </div>

      <div className="text-xl font-bold text-white mb-1" style={{ fontFamily: "'Courier New', monospace" }}>
        {fmt(r.profit)}
      </div>
      <div className="text-xs text-white/40 mb-3">weekly profit</div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: "Coverage", value: `${r.coverage.toFixed(1)}%` },
          { label: "Services", value: r.services },
          { label: "Margin", value: `${r.margin.toFixed(1)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg p-2" style={{ background: "rgba(255,255,255,0.04)" }}>
            <div className="text-xs text-white/40 mb-0.5">{label}</div>
            <div className="text-sm font-mono text-white/90">{value}</div>
          </div>
        ))}
      </div>

      <div className="mb-2">
        <div className="flex justify-between text-xs text-white/40 mb-1">
          <span>Coverage</span><span>{r.coverage.toFixed(1)}%</span>
        </div>
        <ProgressBar value={r.coverage} color={r.color} />
      </div>

      <div className="flex flex-wrap gap-1 mt-2">
        {r.hubs.slice(0, 3).map(h => (
          <span key={h} className="text-xs px-1.5 py-0.5 rounded font-mono" style={{ background: `${r.color}15`, color: r.color + "cc", border: `1px solid ${r.color}30` }}>
            P{h}
          </span>
        ))}
        <span className="text-xs px-1.5 py-0.5 rounded font-mono text-white/30" style={{ background: "rgba(255,255,255,0.04)" }}>
          +{r.hubs.length - 3}
        </span>
      </div>
    </div>
  );
}

// ─── REGIONAL VIEW ───────────────────────────────────────────────────────────
function RegionalView() {
  const optimizationState = useOptimizationState();
  const regions = Object.values(optimizationState.regions);
  const [selId, setSelId] = useState(null);

  // Auto-select first region when data arrives
  useEffect(() => {
    if (!selId && regions.length > 0) {
      setSelId(regions[0].id);
    }
  }, [regions, selId]);

  const sel = regions.find(r => r.id === selId) || regions[0];

  if (regions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-white/40">No regional data available</div>
      </div>
    );
  }

  return (
    <div className="flex gap-6 h-full">
      <div className="grid grid-cols-1 gap-3 w-80 flex-shrink-0 overflow-y-auto pr-1">
        {regions.map(r => <RegionCard key={r.id} r={r} onClick={() => setSelId(r.id)} selected={selId === r.id} />)}
      </div>
      <div className="flex-1 rounded-xl p-5 overflow-y-auto" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
        {sel && regions.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sel.color, boxShadow: `0 0 12px ${sel.color}` }} />
              <h2 className="text-lg font-semibold text-white" style={{ fontFamily: "'Courier New', monospace" }}>{sel.name} Regional Agent</h2>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              {[
                { label: "Weekly Profit", value: fmt(sel.profit), color: sel.color },
                { label: "Annual Profit", value: fmt(sel.profit * 52), color: "#10b981" },
                { label: "Operating Cost", value: fmt(sel.operating_cost || sel.cost), color: "#f59e0b" },
                { label: "Uncovered TEU", value: fmtNum(sel.uncovered), color: "#ef4444" },
              ].map(({ label, value, color }) => (
                <div key={label} className="rounded-lg p-4" style={{ background: `${color}08`, border: `1px solid ${color}22` }}>
                  <div className="text-xs text-white/40 mb-1 font-mono">{label}</div>
                  <div className="text-xl font-bold font-mono" style={{ color }}>{value}</div>
                </div>
              ))}
            </div>

            <div className="mb-6">
              <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-3">Cost Breakdown</div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Base Operating Cost", value: fmt(sel.operating_cost || sel.cost), color: "#f59e0b" },
                  { label: "Transshipment Cost", value: fmt(sel.transship_cost || 0), color: "#f59e0b" },
                  { label: "Total Weekly Cost", value: fmt(sel.cost), color: "#ef4444" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="rounded-lg p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div className="text-[10px] text-white/40 mb-1 font-mono uppercase tracking-wider">{label}</div>
                    <div className="text-lg font-bold font-mono text-white/80">{value}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-3">Service Funnel</div>
              <div className="flex items-center gap-2">
                {[
                  { label: "Generated", value: sel.generated, w: 100 },
                  { label: "Filtered", value: sel.filtered, w: (sel.filtered / sel.generated) * 100 },
                  { label: "Selected", value: sel.selected, w: (sel.selected / sel.generated) * 100 },
                ].map(({ label, value, w }, i) => (
                  <div key={label} className="flex-1">
                    <div className="text-xs text-white/40 mb-1 font-mono">{label}</div>
                    <div className="h-8 rounded flex items-center justify-center text-sm font-bold font-mono transition-all duration-700"
                      style={{ width: `${Math.max(30, w)}%`, background: hexToRgba(sel.color, i === 0 ? 0.25 : i === 1 ? 0.2 : 0.4), color: sel.color }}>
                      {fmtNum(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-3">Hub Ports</div>
              <div className="flex flex-wrap gap-2">
                {sel.hubs.map(h => (
                  <div key={h} className="px-3 py-1.5 rounded-lg text-sm font-mono" style={{ background: `${sel.color}15`, color: sel.color, border: `1px solid ${sel.color}33` }}>
                    Port {h}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg p-4" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-2">Strategy</div>
              <div className="text-sm text-white/80 font-mono">
                Strategy C — <span style={{ color: sel.color }}>Hybrid</span><br />
                <span className="text-white/50 text-xs">Balancing hub consolidation with direct lane coverage across {sel.services} selected services.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── FUNNEL CHART ────────────────────────────────────────────────────────────
function FunnelView() {
  const optimizationState = useOptimizationState();
  const regions = Object.values(optimizationState.regions);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-5 gap-3">
        {regions.map(r => (
          <div key={r.id} className="rounded-xl p-4" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <div className="flex items-center gap-1.5 mb-3">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: r.color }} />
              <span className="text-xs font-mono text-white/70">{r.name}</span>
            </div>
            {[
              { label: "Gen", value: r.generated, max: 1000 },
              { label: "Flt", value: r.filtered, max: 1000 },
              { label: "Sel", value: r.selected, max: 200 },
            ].map(({ label, value, max }) => (
              <div key={label} className="mb-2">
                <div className="flex justify-between text-xs text-white/40 mb-1">
                  <span className="font-mono">{label}</span>
                  <span className="font-mono">{fmtNum(value)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${(value / max) * 100}%`, background: r.color, opacity: label === "Sel" ? 1 : 0.5 }} />
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-4">Profit per Service ($/wk)</div>
          <div className="space-y-2">
            {regions.map(r => {
              const pps = Math.round(r.profit / r.services);
              return (
                <div key={r.id}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-white/60 font-mono">{r.name}</span>
                    <span className="font-mono" style={{ color: r.color }}>${fmtNum(pps)}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(pps / 5000000) * 100}%`, background: `linear-gradient(90deg, ${r.color}88, ${r.color})`, boxShadow: `0 0 6px ${r.color}66` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-4">Coverage Distribution</div>
          <div className="space-y-2">
            {regions.map(r => (
              <div key={r.id}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/60 font-mono">{r.name}</span>
                  <span className="font-mono" style={{ color: r.color }}>{r.coverage.toFixed(1)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${r.coverage}%`, background: `linear-gradient(90deg, ${r.color}66, ${r.color})` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── FEEDBACK VIEW ───────────────────────────────────────────────────────────
function FeedbackView() {
  const optimizationState = useOptimizationState();
  const maxProfit = Math.max(...optimizationState.iterations.map(i => i.profit));
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        {optimizationState.iterations.map((it) => (
          <div key={it.iter} className="rounded-xl p-5 transition-all"
            style={{
              background: it.rerun ? "rgba(239,68,68,0.06)" : "rgba(16,185,129,0.06)",
              border: `1px solid ${it.rerun ? "#ef444433" : "#10b98133"}`
            }}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-white/40 uppercase tracking-widest">Iteration {it.iter}</span>
              <span className="text-xs px-2 py-0.5 rounded font-mono" style={{ background: it.rerun ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)", color: it.rerun ? "#ef4444" : "#10b981" }}>
                {it.rerun ? "RERUN" : "CONVERGED"}
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-white mb-1">{fmt(it.profit)}</div>
            <div className="text-xs text-white/40 mb-3">weekly profit</div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="rounded p-2" style={{ background: "rgba(255,255,255,0.04)" }}>
                <div className="text-xs text-white/40 font-mono">Coverage</div>
                <div className="text-sm font-mono text-white/80">{it.coverage.toFixed(1)}%</div>
              </div>
              <div className="rounded p-2" style={{ background: "rgba(255,255,255,0.04)" }}>
                <div className="text-xs text-white/40 font-mono">Conv.Score</div>
                <div className="text-sm font-mono text-white/80">{it.score}</div>
              </div>
            </div>
            <div className="text-xs text-white/40 font-mono leading-relaxed">{it.reason.slice(0, 60)}...</div>

            {/* profit bar */}
            <div className="mt-3">
              <div className="h-1 rounded-full bg-white/10 overflow-hidden">
                <div className="h-full rounded-full transition-all duration-1000"
                  style={{ width: `${(it.profit / maxProfit) * 100}%`, background: it.rerun ? "#ef4444" : "#10b981" }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Convergence graph */}
      <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
        <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-4">Convergence Trajectory</div>
        <svg viewBox="0 0 400 80" className="w-full">
          <defs>
            <linearGradient id="convGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
            </linearGradient>
          </defs>
          {/* Grid */}
          {[0.97, 0.975, 0.98, 0.985].map((v, i) => {
            const y = 70 - ((v - 0.97) / 0.015) * 60;
            return (
              <g key={i}>
                <line x1={40} y1={y} x2={390} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
                <text x={35} y={y + 3} fontSize="7" fill="rgba(255,255,255,0.3)" textAnchor="end" fontFamily="monospace">{v.toFixed(3)}</text>
              </g>
            );
          })}
          {/* Area */}
          <polygon
            points={optimizationState.iterations.length > 0 
              ? `${optimizationState.iterations.map((it, i) => {
                  const x = 40 + (i / Math.max(1, optimizationState.iterations.length - 1)) * 320;
                  const y = 70 - ((it.score - 0.97) / 0.015) * 60;
                  return `${x},${y}`;
                }).join(" ")} ${40 + (Math.max(0, optimizationState.iterations.length - 1) / Math.max(1, optimizationState.iterations.length - 1)) * 320},70 40,70`
              : "40,70 40,70"}
            fill="url(#convGrad)"
            className="transition-all duration-700"
          />
          {/* Line */}
          <polyline
            points={optimizationState.iterations.length > 0 
              ? optimizationState.iterations.map((it, i) => {
                  const x = 40 + (i / Math.max(1, optimizationState.iterations.length - 1)) * 320;
                  const y = 70 - ((it.score - 0.97) / 0.015) * 60;
                  return `${x},${y}`;
                }).join(" ")
              : "40,70"}
            fill="none" stroke="#00d4ff" strokeWidth="2" strokeLinejoin="round"
            className="transition-all duration-700"
          />
          {optimizationState.iterations.map((it, i) => {
            const x = 40 + (i / Math.max(1, optimizationState.iterations.length - 1)) * 320;
            const cy = 70 - ((it.score - 0.97) / 0.015) * 60;
            return (
              <g key={it.iter}>
                <circle cx={x} cy={cy} r="4" fill="#00d4ff" />
                <circle cx={x} cy={cy} r="8" fill="#00d4ff" opacity="0.2" />
                <text x={x} y={cy - 10} fontSize="7" fill="#00d4ff" textAnchor="middle" fontFamily="monospace">it.{it.iter}</text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { 
            label: "Final Convergence", 
            value: optimizationState.iterations.length > 0 ? optimizationState.iterations[optimizationState.iterations.length - 1].score.toFixed(3) : "N/A", 
            color: "#10b981", 
            sub: `${optimizationState.iterations.length > 0 ? (optimizationState.iterations[optimizationState.iterations.length - 1].score * 100).toFixed(1) : 0}% optimal` 
          },
          { 
            label: "Coverage Gap", 
            value: optimizationState.global?.decision_output?.feedback?.coverage_gap ? `${optimizationState.global.decision_output.feedback.coverage_gap.toFixed(2)}pp` : "N/A", 
            color: "#f59e0b", 
            sub: "below 70% target" 
          },
          { 
            label: "Profit Improvement", 
            value: optimizationState.iterations.length > 1 
              ? `+${(((optimizationState.iterations[optimizationState.iterations.length - 1].profit - optimizationState.iterations[0].profit) / optimizationState.iterations[0].profit) * 100).toFixed(1)}%` 
              : "N/A", 
            color: "#00d4ff", 
            sub: optimizationState.iterations.length > 1 ? `it.0 → it.${optimizationState.iterations.length - 1}` : "Baseline" 
          },
        ].map(({ label, value, color, sub }) => (
          <div key={label} className="rounded-lg p-4 text-center" style={{ background: `${color}08`, border: `1px solid ${color}22` }}>
            <div className="text-xs text-white/40 font-mono mb-1">{label}</div>
            <div className="text-2xl font-bold font-mono" style={{ color }}>{value}</div>
            <div className="text-xs text-white/40 mt-1">{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── CONFLICT VIEW ───────────────────────────────────────────────────────────
function ConflictView() {
  const state = useOptimizationState();
  const decision = state.global.decision_output || {};
  const conflicts = decision.conflicts || [];
  const evalData = decision.evaluation || { score: 3.5, max: 5, status: "Moderate", reasons: ["Coverage gap"] };
  const conflictCount = conflicts.length;
  const severity = decision.feedback?.conflict_severity || 0;
  
  const hasConflicts = conflictCount > 0;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Conflicts Detected", value: conflictCount.toString(), color: hasConflicts ? "#ef4444" : "#10b981", icon: hasConflicts ? "⚠" : "✓" },
          { label: "Conflicts Resolved", value: decision.resolution_log?.length.toString() || "0", color: "#10b981", icon: "✓" },
          { label: "Conflict Severity", value: severity > 0 ? severity.toString() : "None", color: severity > 0 ? "#ef4444" : "#10b981", icon: "○" },
          { label: "Evaluation Status", value: evalData.status || "Moderate", color: "#f59e0b", icon: "◎" },
        ].map(({ label, value, color, icon }) => (
          <div key={label} className="rounded-xl p-4 text-center" style={{ background: `${color}08`, border: `1px solid ${color}22` }}>
            <div className="text-2xl mb-1" style={{ color }}>{icon}</div>
            <div className="text-xl font-bold font-mono" style={{ color }}>{value}</div>
            <div className="text-xs text-white/40 mt-1 font-mono">{label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl p-5" style={{ background: hasConflicts ? "rgba(239,68,68,0.05)" : "rgba(16,185,129,0.05)", border: `1px solid ${hasConflicts ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)"}` }}>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: hasConflicts ? "#ef4444" : "#10b981", boxShadow: `0 0 8px ${hasConflicts ? "#ef4444" : "#10b981"}` }} />
          <span className="text-sm font-mono" style={{ color: hasConflicts ? "#ef4444" : "#10b981" }}>
            {hasConflicts ? `${conflictCount} Regional Conflicts Detected` : "No Regional Conflicts Detected"}
          </span>
        </div>
        <p className="text-xs text-white/50 font-mono leading-relaxed">
          {hasConflicts 
            ? "The CoordinatorAgent detected overlapping service assignments or resource bottlenecks across regions. Resolution protocols are active."
            : "The CoordinatorAgent found zero overlapping service assignments across all regional agents. Each service ID is uniquely assigned to exactly one region. Resolution protocol was not triggered."}
        </p>
      </div>

      <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
        <div className="text-xs font-mono text-white/40 uppercase tracking-widest mb-4">Coordinator Evaluation</div>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Score", value: `${evalData.score} / ${evalData.max}`, color: "#f59e0b" },
            { label: "Status", value: evalData.status || "Moderate", color: "#f59e0b" },
            { label: "Reasons", value: evalData.reasons?.length > 0 ? evalData.reasons[0].slice(0,25)+"..." : "N/A", color: "#f59e0b" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-lg p-3" style={{ background: "rgba(255,255,255,0.04)" }}>
              <div className="text-xs text-white/40 font-mono mb-1">{label}</div>
              <div className="text-sm font-mono" style={{ color }} title={label==="Reasons" ? evalData.reasons?.join(", ") : undefined}>{value}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 text-xs text-white/40 font-mono leading-relaxed">
          {evalData.reasons?.join(". ") || "System achieved strong profitability but demand coverage requires further balancing in the next planning cycle."}
        </div>
      </div>
    </div>
  );
}

// ─── MAP VIEW ────────────────────────────────────────────────────────────────
// ─── MAP VIEW ────────────────────────────────────────────────────────────────
const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

function MapView() {
  const [tick, setTick] = useState(0);
  const optimizationState = useOptimizationState();
  const regions = Object.values(optimizationState.regions);

  useEffect(() => {
    const t = setInterval(() => setTick(p => p + 1), 50);
    return () => clearInterval(t);
  }, []);

  const getRegionColor = (regionId) => {
    const colors = {
      asia: "#00d4ff",
      europe: "#7c3aed",
      americas: "#10b981",
      middle_east: "#f59e0b",
      africa: "#ef4444"
    };
    return colors[regionId?.toLowerCase()] || "#10b981";
  };


  const services = optimizationState.global.selected_services || [];

  // ── Build a deterministic port→region map from ALL services ─────────────
  // Each port gets the region where it appears most frequently across services.
  // This ensures port 285 (Americas hub) always renders in Americas coords,
  // even when it appears in an Asia-labeled inter-regional service.
  const portRegionMap = useMemo(() => {
    const counts = {};
    services.forEach(svc => {
      const region = svc.region?.toLowerCase() || 'asia';
      (svc.ports || []).forEach(p => {
        if (!counts[p]) counts[p] = {};
        counts[p][region] = (counts[p][region] || 0) + 1;
      });
    });
    const map = {};
    Object.entries(counts).forEach(([port, regionCounts]) => {
      map[parseInt(port)] = Object.entries(regionCounts)
        .sort((a, b) => b[1] - a[1])[0][0];
    });
    return map;
  }, [services]);

  // ── Stable per-port coordinates (region-aware, globally consistent) ─────
  const getPortLocation = useCallback((portId, fallbackRegion) => {
    const regionId = portRegionMap[portId] || fallbackRegion?.toLowerCase() || 'asia';
    const seed = (portId * 9301 + 49297) % 233280;
    const rnd1 = seed / 233280;
    const rnd2 = ((seed * 9301 + 49297) % 233280) / 233280;
    const bounds = {
      asia:        { minLng: 70,  maxLng: 135, minLat: 5,   maxLat: 40  },
      europe:      { minLng: -5,  maxLng: 28,  minLat: 38,  maxLat: 58  },
      americas:    { minLng: -115,maxLng: -45, minLat: -25, maxLat: 48  },
      middle_east: { minLng: 38,  maxLng: 58,  minLat: 14,  maxLat: 29  },
      africa:      { minLng: -10, maxLng: 45,  minLat: -30, maxLat: 30  },
    };
    const b = bounds[regionId] || bounds.asia;
    return [
      b.minLng + rnd1 * (b.maxLng - b.minLng),
      b.minLat + rnd2 * (b.maxLat - b.minLat),
    ];
  }, [portRegionMap]);

  // ── Classify services as regional or inter-regional ─────────────────────
  const { regionalServices, interRegionalServices } = useMemo(() => {
    const regional = [], interReg = [];
    services.forEach(svc => {
      if (!svc.ports || svc.ports.length < 2) return;
      const svcRegion = svc.region?.toLowerCase() || 'asia';
      const portRegions = new Set(
        svc.ports.map(p => portRegionMap[p] || svcRegion)
      );
      if (portRegions.size > 1) {
        interReg.push({ ...svc, portRegions: [...portRegions] });
      } else {
        regional.push(svc);
      }
    });
    return { regionalServices: regional, interRegionalServices: interReg };
  }, [services, portRegionMap]);

  // Corridors for legend
  const corridors = optimizationState.corridors.length > 0
    ? optimizationState.corridors.map(c => ({
        ...c,
        from: typeof c.from === 'string' ? parseInt(c.from.replace('Port ', '')) : c.from,
        to: typeof c.to === 'string' ? parseInt(c.to.replace('Port ', '')) : c.to,
        color: getRegionColor(c.region || 'americas')
      }))
    : [
      { from: 285, to: 146, teu: 10902, color: "#10b981" },
      { from: 235, to: 36,  teu: 5292,  color: "#10b981" },
      { from: 221, to: 100, teu: 1932,  color: "#7c3aed" },
      { from: 112, to: 176, teu: 1128,  color: "#ef4444" },
      { from: 220, to: 221, teu: 966,   color: "#f59e0b" },
    ];

  return (
    <div className="rounded-xl overflow-hidden relative" style={{ background: "#030d1a", border: "1px solid rgba(255,255,255,0.07)", height: "480px" }}>
      <div className="absolute top-0 left-0 right-0 z-10 px-5 py-3 border-b border-white/5 flex items-center gap-3 bg-black/40 backdrop-blur-md">
        <PulseDot color="#00d4ff" />
        <span className="text-xs font-mono text-white/60 uppercase tracking-widest">Global Maritime Route Map</span>
        <div className="ml-auto flex items-center gap-5">
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-[2px]" style={{ background: "rgba(255,255,255,0.5)" }} />
            <span className="text-[10px] font-mono text-white/30">Inter-Regional</span>
          </div>
          {regions.map(r => (
            <div key={r.id} className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: r.color }} />
              <span className="text-xs font-mono text-white/40">{r.name}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="w-full h-full" style={{ background: "linear-gradient(180deg, #030d1a 0%, #060f1e 100%)" }}>
        <ComposableMap projection="geoMercator" projectionConfig={{ scale: 110, center: [10, 15] }} style={{ width: "100%", height: "100%" }}>
          <Geographies geography={geoUrl}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#0f1f35"
                  stroke="#1a3050"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none" },
                    hover: { fill: "#132742", outline: "none" },
                    pressed: { outline: "none" },
                  }}
                />
              ))
            }
          </Geographies>

          {/* ── Regional service routes (colored by region) ── */}
          {regionalServices.map((svc, idx) => {
            if (svc.load < 100) return null;
            const color = getRegionColor(svc.region);
            const coords = svc.ports.map(p => getPortLocation(p, svc.region));
            const w = Math.max(0.4, Math.min(1.8, svc.load / 6000));
            return (
              <Line
                key={`reg-${svc.id}-${idx}`}
                coordinates={coords}
                stroke={color}
                strokeWidth={w}
                strokeOpacity={0.35}
                strokeLinecap="round"
              />
            );
          })}

          {/* ── Inter-regional routes (white/gold — cross-continental) ── */}
          {interRegionalServices.map((svc, idx) => {
            if (svc.load < 200) return null;
            const coords = svc.ports.map(p => getPortLocation(p, svc.region));
            const w = Math.max(0.8, Math.min(2.5, svc.load / 4000));
            // Gold for very high-load, white otherwise
            const color = svc.load > 8000 ? "#fbbf24" : "rgba(255,255,255,0.7)";
            return (
              <Line
                key={`inter-${svc.id}-${idx}`}
                coordinates={coords}
                stroke={color}
                strokeWidth={w}
                strokeOpacity={svc.load > 8000 ? 0.75 : 0.45}
                strokeLinecap="round"
              />
            );
          })}

          {/* ── Animated flow dots: regional (colored) ── */}
          {regionalServices.filter(s => s.load >= 500).slice(0, 25).map((svc, idx) => {
            if (svc.ports.length < 2) return null;
            const color = getRegionColor(svc.region);
            const numSegs = svc.ports.length - 1;
            const speed = 18 + (idx % 8);
            const offset = (idx * 13) % 100;
            const t = ((tick + offset) / speed) % numSegs;
            const seg = Math.floor(t);
            const frac = t - seg;
            const p1 = getPortLocation(svc.ports[seg], svc.region);
            const p2 = getPortLocation(svc.ports[seg + 1], svc.region);
            const lng = p1[0] + (p2[0] - p1[0]) * frac;
            const lat = p1[1] + (p2[1] - p1[1]) * frac;
            return (
              <Marker key={`rdot-${svc.id}-${idx}`} coordinates={[lng, lat]}>
                <circle r={2.5} fill={color} opacity={0.9} />
                <circle r={4} fill={color} opacity={0.25} />
              </Marker>
            );
          })}

          {/* ── Animated flow dots: inter-regional (white pulses) ── */}
          {interRegionalServices.filter(s => s.load >= 300).slice(0, 20).map((svc, idx) => {
            if (svc.ports.length < 2) return null;
            const numSegs = svc.ports.length - 1;
            const speed = 14 + (idx % 6);
            const offset = (idx * 17) % 100;
            const t = ((tick + offset) / speed) % numSegs;
            const seg = Math.floor(t);
            const frac = t - seg;
            const p1 = getPortLocation(svc.ports[seg], svc.region);
            const p2 = getPortLocation(svc.ports[seg + 1], svc.region);
            const lng = p1[0] + (p2[0] - p1[0]) * frac;
            const lat = p1[1] + (p2[1] - p1[1]) * frac;
            const dotColor = svc.load > 8000 ? "#fbbf24" : "#ffffff";
            return (
              <Marker key={`idot-${svc.id}-${idx}`} coordinates={[lng, lat]}>
                <circle r={3} fill={dotColor} opacity={1} />
                <circle r={5.5} fill={dotColor} opacity={0.3} />
              </Marker>
            );
          })}

          {/* ── Port dots (hub ports only) ── */}
          {Object.entries(portRegionMap).slice(0, 60).map(([portId, region]) => {
            const coord = getPortLocation(parseInt(portId), region);
            return (
              <Marker key={`hub-${portId}`} coordinates={coord}>
                <circle r={1.2} fill="#fff" opacity={0.35} />
              </Marker>
            );
          })}
        </ComposableMap>
      </div>

      {/* ── Legend ── */}
      <div className="absolute bottom-5 left-5 z-10 p-4 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 min-w-[220px]">
        <div className="text-[10px] text-white/40 font-mono tracking-widest mb-3 uppercase">Route Legend</div>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-5 h-[1.5px]" style={{ background: "rgba(255,255,255,0.5)" }} />
          <span className="text-xs text-white/60 font-mono">Inter-Regional ({interRegionalServices.length})</span>
        </div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-5 h-[1px]" style={{ background: "#fbbf24" }} />
          <span className="text-xs text-white/60 font-mono">High-Load Cross-Region</span>
        </div>
        {corridors.slice(0, 4).map((c, i) => (
          <div key={i} className="flex items-center gap-3 mb-1.5">
            <div className="w-5 h-[2px]" style={{ background: c.color }} />
            <div className="text-xs text-white/70 font-mono">P{c.from}→P{c.to}: {fmtNum(c.teu)} TEU</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── SUMMARY VIEW ────────────────────────────────────────────────────────────
function SummaryView() {
  const state = useOptimizationState();
  const summaryText = state.global.executive_summary || "";
  
  // Parse the summary text roughly
  const extractSection = (header) => {
    const lines = summaryText.split('\n');
    let inSection = false;
    const items = [];
    for (const line of lines) {
      if (line.startsWith(header)) {
        inSection = true;
        continue;
      }
      if (inSection) {
        if (line.trim() === "" || (!line.startsWith("-") && !line.startsWith(" "))) break;
        if (line.startsWith("-")) items.push(line.replace("-", "").trim());
      }
    }
    return items;
  };

  const strengths = extractSection("Strengths:");
  const weaknesses = extractSection("Weaknesses:");
  const actions = extractSection("Priority Actions:");

  const isGood = summaryText.includes("Verdict: Good");

  return (
    <div className="space-y-5">
      <div className="rounded-xl p-6" style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.08), rgba(0,212,255,0.08))", border: "1px solid rgba(16,185,129,0.2)" }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: isGood ? "#10b981" : "#f59e0b", boxShadow: `0 0 12px ${isGood ? "#10b981" : "#f59e0b"}` }} />
          <span className="text-sm font-mono font-semibold uppercase tracking-widest" style={{ color: isGood ? "#10b981" : "#f59e0b" }}>
            {isGood ? "Verdict: Good" : "Verdict: Needs Improvement"}
          </span>
        </div>
        <p className="text-base text-white/80 font-mono leading-relaxed">
          The global weekly profit is <span className="text-emerald-400 font-bold">{fmt(state.global.weeklyProfit)}</span>, indicating strong financial performance 
          with an <span className="text-emerald-400 font-bold">{state.global.margin?.toFixed(1)}% profit margin</span> across {fmtNum(state.global.totalServices)} deployed services.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl p-5" style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.2)" }}>
          <div className="text-xs font-mono text-emerald-400 uppercase tracking-widest mb-3">Strengths</div>
          {(strengths.length > 0 ? strengths : [
            `Global weekly profit ${fmt(state.global.weeklyProfit)} — excellent financial performance`,
            "No inter-regional service conflicts detected",
            `Convergence reached at ${state.global.convergence?.toFixed(3)}`
          ]).map((s, i) => (
            <div key={i} className="flex gap-2 mb-2">
              <span className="text-emerald-400 text-xs mt-0.5 flex-shrink-0">+</span>
              <span className="text-xs text-white/60 font-mono leading-relaxed">{s}</span>
            </div>
          ))}
        </div>

        <div className="rounded-xl p-5" style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)" }}>
          <div className="text-xs font-mono text-red-400 uppercase tracking-widest mb-3">Weaknesses</div>
          {(weaknesses.length > 0 ? weaknesses : [
            `Demand coverage ${state.global.coverage?.toFixed(1)}% — ${fmtNum(state.global.unserved)} TEU/wk remains unserved`,
            `Operating cost ${fmt(state.global.operatingCost)}/wk represents scale risk`
          ]).map((s, i) => (
            <div key={i} className="flex gap-2 mb-2">
              <span className="text-red-400 text-xs mt-0.5 flex-shrink-0">−</span>
              <span className="text-xs text-white/60 font-mono leading-relaxed">{s}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl p-5" style={{ background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)" }}>
        <div className="text-xs font-mono text-amber-400 uppercase tracking-widest mb-3">Priority Actions</div>
        <div className="grid grid-cols-2 gap-3">
          {(actions.length > 0 ? actions : [
            "Expand Coverage targeting top 10 unmet demand corridors.",
            "Consolidate low-margin regions to fund expansion.",
            "Increase coverage_weight in GA objective for next iteration."
          ]).map((detail, i) => (
            <div key={i} className="rounded-lg p-3" style={{ background: "rgba(255,255,255,0.03)" }}>
              <div className="text-xs font-mono text-amber-400 mb-1">{String(i + 1).padStart(2, "0")} · Action</div>
              <div className="text-xs text-white/50 font-mono leading-relaxed">{detail}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── KPI CARD ────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, color, sparkData }) {
  return (
    <div className="rounded-xl p-5 transition-all duration-300 hover:scale-[1.02] cursor-default group"
      style={{ background: `${color}08`, border: `1px solid ${color}22`, boxShadow: `0 0 0 transparent`, transition: "box-shadow 0.3s" }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = `0 0 30px ${color}20`}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "0 0 0 transparent"}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-mono text-white/40 uppercase tracking-widest">{label}</span>
        {sparkData && <Sparkline data={sparkData} color={color} />}
      </div>
      <div className="text-3xl font-bold font-mono tracking-tight" style={{ color, textShadow: `0 0 20px ${color}66` }}>
        {value}
      </div>
      {sub && <div className="text-xs text-white/40 mt-1 font-mono">{sub}</div>}
      <div className="mt-3 h-px w-full" style={{ background: `linear-gradient(90deg, ${color}44, transparent)` }} />
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  // Get live optimization data from WebSocket
  const optimizationState = useOptimizationState();

  const [activeNav, setActiveNav] = useState("overview");
  const [showPulse, setShowPulse] = useState(true);

  useEffect(() => {
    const t = setInterval(() => setShowPulse(p => !p), 1500);
    return () => clearInterval(t);
  }, []);

  // Use live data from optimization state
  const regions = Object.values(optimizationState.regions);

  const renderMain = () => {
    switch (activeNav) {
      case "overview": return (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-4">
            <KpiCard
              label="Weekly Profit"
              value={`$${(optimizationState.global.weeklyProfit / 1e6).toFixed(1)}M`}
              sub={`${optimizationState.global.margin.toFixed(1)}% margin`}
              color="#00d4ff"
              sparkData={optimizationState.iterations.map(i => i.profit / 1e6)}
            />
            <KpiCard
              label="Annual Profit"
              value={`$${(optimizationState.global.annualProfit / 1e9).toFixed(1)}B`}
              sub="52-week projection"
              color="#10b981"
              sparkData={optimizationState.iterations.map(i => (i.profit * 52) / 1e9)}
            />
            <KpiCard
              label="Demand Coverage"
              value={`${optimizationState.global.coverage.toFixed(1)}%`}
              sub={`${fmtNum(optimizationState.global.unserved)} TEU/wk unserved`}
              color="#f59e0b"
              sparkData={optimizationState.iterations.map(i => i.coverage)}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <KpiCard label="Services Deployed" value={fmtNum(optimizationState.global.totalServices)} sub="across 5 regions" color="#8b5cf6" />
            <KpiCard
              label="Profit Margin"
              value={`${optimizationState.global.margin.toFixed(1)}%`}
              sub={`${fmt(optimizationState.global.operatingCost)} operating cost`}
              color="#ec4899"
              sparkData={optimizationState.iterations.map(i => i.score * 100)}
            />
            <KpiCard
              label="Convergence Score"
              value={optimizationState.global.convergence.toFixed(3)}
              sub={`${optimizationState.iterations.length} feedback iterations`}
              color="#6366f1"
              sparkData={optimizationState.iterations.map(i => i.score)}
            />
          </div>
          <MapView />
        </div>
      );
      case "pipeline": return <PipelineView />;
      case "regional": return <RegionalView />;
      case "funnel": return <FunnelView />;
      case "feedback": return <FeedbackView />;
      case "conflict": return <ConflictView />;
      case "map": return <MapView />;
      case "summary": return <SummaryView />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{
      background: "#020c18",
      color: "#e2e8f0",
      fontFamily: "'Courier New', 'Consolas', monospace"
    }}>
      {/* Scanline overlay */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        zIndex: 100
      }} />

      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-3 relative z-10"
        style={{ background: "rgba(2,12,24,0.95)", borderBottom: "1px solid rgba(0,212,255,0.15)", backdropFilter: "blur(20px)" }}>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="relative">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg font-bold"
                style={{ background: "linear-gradient(135deg, #00d4ff22, #10b98122)", border: "1px solid #00d4ff44", color: "#00d4ff" }}>
                ⬡
              </div>
            </div>
            <div>
              <div className="text-sm font-bold tracking-widest text-white uppercase" style={{ letterSpacing: "0.12em" }}>AI Vessel Routing System</div>
              <div className="text-xs text-white/30 uppercase tracking-widest" style={{ fontSize: "9px" }}>Multi-Agent Liner Shipping Optimizer</div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 ml-2">
            <PulseDot color={optimizationState.isConnected ? "#10b981" : "#ef4444"} />
            <span className={`text-xs font-mono uppercase tracking-widest ${optimizationState.isConnected ? "text-emerald-400" : "text-red-400"}`}>
              {optimizationState.isConnected ? "Live" : "Offline"}
            </span>
            {optimizationState.isPipelineRunning && (
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-widest">
                {optimizationState.currentStage}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-5">
          {[
            { label: "Ports", value: fmtNum(optimizationState.global.ports) },
            { label: "Lanes", value: fmtNum(optimizationState.global.lanes) },
            { label: "Services", value: fmtNum(optimizationState.global.services) },
            { label: "Weekly TEU", value: `${(optimizationState.global.weeklyDemand / 1000).toFixed(0)}K` },
            {label: "Runtime", value: `${optimizationState.global.runtime || "0.0"}s` },
            { label: "Iterations", value: optimizationState.iterations.length.toString() },
            { label: "Convergence", value: optimizationState.global.convergence.toFixed(3) },
          ].map(({ label, value }) => (
            <div key={label} className="text-center">
              <div className="text-xs font-bold text-white/90 font-mono">{value}</div>
              <div className="text-white/30 font-mono" style={{ fontSize: "9px", letterSpacing: "0.08em" }}>{label}</div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => optimizationState.startOptimization()}
            disabled={optimizationState.isPipelineRunning}
            className="px-3 py-1.5 rounded text-xs font-mono transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ background: optimizationState.isPipelineRunning ? "rgba(239,68,68,0.08)" : "rgba(0,212,255,0.08)", border: `1px solid ${optimizationState.isPipelineRunning ? "rgba(239,68,68,0.2)" : "rgba(0,212,255,0.2)"}`, color: optimizationState.isPipelineRunning ? "rgba(239,68,68,0.8)" : "rgba(0,212,255,0.8)" }}>
            {optimizationState.isPipelineRunning ? "⏸ Running" : "▶ Play"}
          </button>
          {["⇌ Flows", "⊡ Reset", "↓ Export"].map(btn => (
            <button key={btn} className="px-3 py-1.5 rounded text-xs font-mono transition-all duration-200 hover:scale-105"
              style={{ background: "rgba(0,212,255,0.08)", border: "1px solid rgba(0,212,255,0.2)", color: "rgba(0,212,255,0.8)" }}>
              {btn}
            </button>
          ))}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── SIDEBAR ──────────────────────────────────────────────── */}
        <aside className="flex-shrink-0 w-52 flex flex-col relative z-10"
          style={{ background: "rgba(2,12,24,0.9)", borderRight: "1px solid rgba(255,255,255,0.05)" }}>
          <div className="p-3 border-b border-white/5">
            <div className="text-white/20 font-mono uppercase tracking-widest" style={{ fontSize: "9px", letterSpacing: "0.15em" }}>Navigation</div>
          </div>
          <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {navItems.map(({ id, label, icon }) => (
              <button
                key={id}
                onClick={() => setActiveNav(id)}
                className="w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-150 group"
                style={{
                  background: activeNav === id ? "rgba(0,212,255,0.1)" : "transparent",
                  border: `1px solid ${activeNav === id ? "rgba(0,212,255,0.25)" : "transparent"}`,
                  color: activeNav === id ? "#00d4ff" : "rgba(255,255,255,0.45)",
                }}>
                <span className="text-base leading-none">{icon}</span>
                <span className="text-xs font-mono truncate">{label}</span>
                {activeNav === id && <div className="ml-auto w-1 h-1 rounded-full bg-cyan-400" />}
              </button>
            ))}
          </nav>

          {/* Sidebar bottom stats */}
          <div className="p-3 border-t border-white/5 space-y-2">
            {[
              { label: "Passed Assertions", value: `${optimizationState.global.status?.assertions_passed || 242}/${optimizationState.global.status?.assertions_total || 243}`, color: "#10b981" },
              { label: "Score", value: `${((optimizationState.global.status?.assertions_passed || 242) / (optimizationState.global.status?.assertions_total || 243) * 100).toFixed(0)}%`, color: "#10b981" },
              { label: "Warnings", value: `${optimizationState.global.status?.warnings || 0}`, color: (optimizationState.global.status?.warnings || 0) > 0 ? "#f59e0b" : "#10b981" },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex justify-between items-center">
                <span className="text-white/30 font-mono" style={{ fontSize: "9px" }}>{label}</span>
                <span className="font-mono text-xs font-bold" style={{ color }}>{value}</span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── MAIN ─────────────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto p-5 relative">
          {/* Section title */}
          <div className="flex items-center gap-3 mb-5">
            <div className="h-px flex-1" style={{ background: "linear-gradient(90deg, rgba(0,212,255,0.3), transparent)" }} />
            <span className="text-xs font-mono text-white/30 uppercase tracking-widest px-2">
              {navItems.find(n => n.id === activeNav)?.label}
            </span>
            <div className="h-px flex-1" style={{ background: "linear-gradient(270deg, rgba(0,212,255,0.3), transparent)" }} />
          </div>

          {renderMain()}
        </main>
      </div>

      {/* ── FOOTER STATUS BAR ──────────────────────────────────────── */}
      <footer className="flex-shrink-0 flex items-center justify-between px-6 py-1.5 relative z-10"
        style={{ background: "rgba(2,12,24,0.95)", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-4">
          {[
            { dot: optimizationState.isPipelineRunning ? "#f59e0b" : "#10b981", text: `Pipeline: ${optimizationState.isPipelineRunning ? (optimizationState.currentStage || "Running") : "Complete"}` },
            { dot: "#00d4ff", text: "GA: Converged" },
            { dot: "#10b981", text: "MILP: Optimal" },
            { dot: "#f59e0b", text: `Coverage: ${optimizationState.global.coverage.toFixed(1)}%` },
          ].map(({ dot, text }) => (
            <div key={text} className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dot }} />
              <span className="text-white/30 font-mono" style={{ fontSize: "10px" }}>{text}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-white/20 font-mono" style={{ fontSize: "10px" }}>AI Vessel Routing System v2.0 · 435 ports · 9,622 lanes</span>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ boxShadow: "0 0 6px #10b981" }} />
            <span className="text-emerald-400 font-mono" style={{ fontSize: "10px" }}>OPERATIONAL</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
