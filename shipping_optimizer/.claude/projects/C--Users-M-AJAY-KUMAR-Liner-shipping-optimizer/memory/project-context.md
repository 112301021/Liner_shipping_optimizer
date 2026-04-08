# 🚢 AI Vessel Routing System — Project Context

---

# 1. 📌 Project Overview

The **AI Vessel Routing System** is a **multi-agent optimization framework** designed to solve large-scale liner shipping network design problems using a hybrid approach combining:

* Genetic Algorithms (GA)
* Mixed Integer Linear Programming (MILP)
* Large Language Models (LLMs)
* Multi-Agent Coordination

The system decomposes a global maritime logistics problem into regional subproblems, optimizes them independently, and then coordinates them through a centralized decision layer with feedback loops.

---

# 2. 🎯 Objective

The primary goal of the system is to:

* Maximize **weekly and annual profit**
* Maximize **demand coverage (%)**
* Minimize **operational and transshipment costs**
* Respect **fleet constraints**
* Ensure **global consistency across regions**

---

# 3. 🧠 Core Idea

The system is not a single optimizer — it is a:

> **Closed-loop, multi-agent optimization controller**

It follows an iterative pipeline:

```
Analyze → Decompose → Optimize → Coordinate → Feedback → Re-optimize
```

---

# 4. 🏗️ System Architecture

## 4.1 High-Level Flow

```
Orchestrator Agent
        ↓
Problem Decomposition
        ↓
Regional Agents (×3)
        ↓
GA + MILP Optimization
        ↓
Coordinator Agent
        ↓
Feedback Loop (Iterative)
        ↓
Final Aggregation + Summary
```

---

## 4.2 Agents Description

### 🔹 Orchestrator Agent

* Entry point of the system
* Performs:

  * Problem analysis (LLM-assisted)
  * Regional decomposition
  * Iterative control loop
  * Final aggregation and reporting

---

### 🔹 Regional Agents

Each region (Asia, Europe, Americas) has its own agent:

Responsibilities:

* Service generation
* Service filtering
* Running optimization:

  * Hierarchical GA (Service + Frequency)
  * MILP flow optimization
* Producing structured outputs

---

### 🔹 Coordinator Agent

Acts as the **decision engine**:

* Detects inter-region conflicts
* Resolves overlapping services
* Evaluates system performance
* Generates feedback signals:

  * Coverage gap
  * Weight adjustments
  * Rerun decisions

---

# 5. ⚙️ Optimization Pipeline

## 5.1 Hierarchical Genetic Algorithm

### Level 1 — Service Selection (`ServiceGA`)

* Selects subset of candidate services
* Fitness considers:

  * Demand satisfaction
  * Revenue potential
  * Operating cost
  * Alignment with demand corridors

---

### Level 2 — Frequency Optimization (`FrequencyGA`)

* Determines sailing frequency per service
* Uses:

  * Route-level demand
  * Capacity matching
  * Overcapacity penalties

---

## 5.2 MILP Flow Optimization (`HubMILP`)

* Allocates flows across services and hubs
* Handles:

  * Direct routing
  * Transshipment flows
* Objective:

  * Maximize profit
  * Penalize unserved demand

---

# 6. 🔁 Feedback Loop (Key Innovation)

The system runs up to **3 iterations**:

### Per iteration:

1. Regional optimization
2. Global aggregation
3. Coordinator evaluation
4. Feedback generation
5. Weight adjustment

---

## Feedback Signals

* `coverage_gap`
* `conflict_severity`
* `weight_adjustments`
* `needs_rerun`

---

## Convergence Criteria

The loop stops when:

* Coverage stabilizes
* No conflicts remain
* No significant improvement

---

# 7. 📊 Key Constraints

### Fleet Constraint

* Total vessels used ≤ fleet size (e.g., 300)

### Demand Satisfaction

* Maximize served TEU
* Penalize unserved demand

### Capacity Constraints

* Service capacity limits
* Port handling limits

---

# 8. 🚀 Efficiency Enhancements (Recent Fixes)

The system includes several optimizations to reduce runtime:

### 1. Early GA Rejection

* Invalid (fleet-violating) solutions are discarded immediately

### 2. GA Early Stopping

* Stops if no improvement for N generations

### 3. Post-GA Fleet Pruning

* Removes inefficient services to satisfy fleet constraint

### 4. MILP Skipping

* Skips MILP when GA output is low quality

### 5. Iteration Early Stop

* Stops feedback loop if no improvement

### 6. Runtime Budget Control

* Limits GA execution time per region

---

# 9. 📈 Output Metrics

The system produces:

## Global Metrics

* Weekly Profit
* Annual Profit
* Total Cost
* Coverage (%)
* Services Selected

---

## Regional Metrics

* Profit per region
* Coverage per region
* Service count
* Cost breakdown

---

## Iteration Trace

* Coverage per iteration
* Profit per iteration
* Convergence score

---

# 10. 🧪 Testing & Validation

The system includes a full pipeline test:

* Validates:

  * Data loading
  * Optimization correctness
  * Constraint satisfaction
  * Feedback loop behavior
* Produces structured output with:

  * Assertions
  * Performance score

---

# 11. 📦 Data Scale

Typical dataset:

* Ports: ~435
* Services: ~1200
* Demand lanes: ~9600
* Weekly demand: ~800,000+ TEU

---

# 12. 🧠 System Characteristics

| Property     | Description                     |
| ------------ | ------------------------------- |
| Type         | Multi-agent optimization system |
| Nature       | Closed-loop adaptive            |
| Optimization | Hybrid (GA + MILP)              |
| Intelligence | LLM-assisted decision layer     |
| Scalability  | High (regional decomposition)   |

---

# 13. ⚠️ Known Challenges

* Large search space (combinatorial)
* MILP computational cost
* Sensitivity to service selection
* Dependency on demand distribution

---

# 14. 🔮 Future Scope

* Parallel regional execution
* Learning-based weight tuning
* Reinforcement learning integration
* Real-time routing adaptation

---

# 15. 🏁 Summary

The system represents a **hybrid AI + operations research approach** to maritime network optimization.

It successfully integrates:

* Heuristic search (GA)
* Exact optimization (MILP)
* Intelligent coordination (LLM agents)

into a unified, scalable, and adaptive framework.

---
