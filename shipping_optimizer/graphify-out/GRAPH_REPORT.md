# Graph Report - .  (2026-04-14)

## Corpus Check
- Corpus is ~23,008 words - fits in a single context window. You may not need a graph.

## Summary
- 365 nodes · 743 edges · 47 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 310 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_GA Optimization & Benchmarking|GA Optimization & Benchmarking]]
- [[_COMMUNITY_Performance & Architecture Config|Performance & Architecture Config]]
- [[_COMMUNITY_Agent & LLM Infrastructure|Agent & LLM Infrastructure]]
- [[_COMMUNITY_Hierarchical Optimization & Agents|Hierarchical Optimization & Agents]]
- [[_COMMUNITY_Evaluation & Orchestration|Evaluation & Orchestration]]
- [[_COMMUNITY_Test Utilities & Reporting|Test Utilities & Reporting]]
- [[_COMMUNITY_Service & Network Loading|Service & Network Loading]]
- [[_COMMUNITY_Step Validation|Step Validation]]
- [[_COMMUNITY_Service GA Operations|Service GA Operations]]
- [[_COMMUNITY_Quality & Verification|Quality & Verification]]
- [[_COMMUNITY_GA Controls Testing|GA Controls Testing]]
- [[_COMMUNITY_GA Controls Validation|GA Controls Validation]]
- [[_COMMUNITY_LLM Metrics|LLM Metrics]]
- [[_COMMUNITY_Frequency GA Analysis|Frequency GA Analysis]]
- [[_COMMUNITY_Frequency GA Evaluation|Frequency GA Evaluation]]
- [[_COMMUNITY_Hub Detection Scoring|Hub Detection Scoring]]
- [[_COMMUNITY_Graph Construction|Graph Construction]]
- [[_COMMUNITY_Flow Optimization|Flow Optimization]]
- [[_COMMUNITY_Service GA Initialization|Service GA Initialization]]
- [[_COMMUNITY_CLAUDE System Principles|CLAUDE System Principles]]
- [[_COMMUNITY_Data Preprocessing|Data Preprocessing]]
- [[_COMMUNITY_Sample Data Utilities|Sample Data Utilities]]
- [[_COMMUNITY_GA Unit Tests|GA Unit Tests]]
- [[_COMMUNITY_LLM Tests|LLM Tests]]
- [[_COMMUNITY_MILP Tests|MILP Tests]]
- [[_COMMUNITY_Regional Agent Tests|Regional Agent Tests]]
- [[_COMMUNITY_Web API Stack|Web API Stack]]
- [[_COMMUNITY_Logging|Logging]]
- [[_COMMUNITY_Clustering Tests|Clustering Tests]]
- [[_COMMUNITY_Data Loader Tests|Data Loader Tests]]
- [[_COMMUNITY_ML Dependencies|ML Dependencies]]
- [[_COMMUNITY_Source Init|Source Init]]
- [[_COMMUNITY_Agents Init|Agents Init]]
- [[_COMMUNITY_Evaluator Manager|Evaluator Manager]]
- [[_COMMUNITY_LLM Init|LLM Init]]
- [[_COMMUNITY_Optimization Init|Optimization Init]]
- [[_COMMUNITY_Optimization Pipeline|Optimization Pipeline]]
- [[_COMMUNITY_Pipeline Orchestration|Pipeline Orchestration]]
- [[_COMMUNITY_Utils Init|Utils Init]]
- [[_COMMUNITY_Tests Init|Tests Init]]
- [[_COMMUNITY_Architect Agent|Architect Agent]]
- [[_COMMUNITY_Reviewer Agent|Reviewer Agent]]
- [[_COMMUNITY_Future Parallel Eval|Future: Parallel Eval]]
- [[_COMMUNITY_Future Adaptive Population|Future: Adaptive Population]]
- [[_COMMUNITY_Runtime Reduction|Runtime Reduction]]
- [[_COMMUNITY_Environment Config|Environment Config]]
- [[_COMMUNITY_Threshold Configuration|Threshold Configuration]]

## God Nodes (most connected - your core abstractions)
1. `Problem` - 43 edges
2. `Service` - 39 edges
3. `Port` - 37 edges
4. `Demand` - 37 edges
5. `ServiceGA` - 34 edges
6. `FrequencyGA` - 33 edges
7. `OrchestratorAgent` - 27 edges
8. `HubDetector` - 25 edges
9. `NetworkLoader` - 20 edges
10. `RegionalAgent` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Verification Before Completion` --semantically_similar_to--> `Output Consistency Validation`  [INFERRED] [semantically similar]
  CLAUDE.md → step1_validation_final_report.md
- `Future: Vectorized Fitness Evaluation (NumPy)` --semantically_similar_to--> `Vectorized Demand Calculation (numpy)`  [INFERRED] [semantically similar]
  PERFORMANCE_OPTIMIZATION_SUMMARY.md → performance_optimizations.md
- `Future: Early Stopping Based on Fitness Convergence` --semantically_similar_to--> `Early Stop Threshold (8 generations)`  [INFERRED] [semantically similar]
  PERFORMANCE_OPTIMIZATION_SUMMARY.md → step1_validation_final_report.md
- `Step1Validator` --uses--> `NetworkLoader`  [INFERRED]
  validate_step1.py → src\data\network_loader.py
- `Step1Validator` --uses--> `OrchestratorAgent`  [INFERRED]
  validate_step1.py → src\agents\orchestrator_agent.py

## Hyperedges (group relationships)
- **Agent Pipeline: Region -> Service -> Deployment -> Profit** — claude_regional_agent, claude_service_generator_agent, claude_deployment_optimizer, claude_profit_evaluator [EXTRACTED 1.00]
- **ServiceGA Optimization Pipeline** — perf_service_ga, perf_service_ga_demand_index, perf_fitness_cache, perf_elite_selection_heapq, perf_duplicate_transshipment_removal [EXTRACTED 1.00]
- **GA Control Validation: Early Stop + Runtime Cap** — step1_early_stop_threshold, step1_runtime_cap, step1_service_ga_controls, step1_frequency_ga_controls [EXTRACTED 1.00]

## Communities

### Community 0 - "GA Optimization & Benchmarking"
Cohesion: 0.13
Nodes (46): benchmark_caching(), benchmark_frequency_ga(), benchmark_service_ga(), create_test_problem(), Benchmark script to demonstrate performance improvements before and after optimi, Benchmark FrequencyGA performance., Demonstrate caching effectiveness., Create a test problem of specified size. (+38 more)

### Community 1 - "Performance & Architecture Config"
Cohesion: 0.05
Nodes (43): Deployment Optimizer, Max Services Constraint (40), Optimizer Agent, Profit Evaluator, Profit Maximization Objective, Regional Agent, Service Generator Agent, Bytes Cache Key (+35 more)

### Community 2 - "Agent & LLM Infrastructure"
Cohesion: 0.09
Nodes (16): ABC, BaseAgent, get_system_prompt(), Base Agent class - parent for all agents, LLMClient, Config, CoordinatorAgent, _parse_json_safe() (+8 more)

### Community 3 - "Hierarchical Optimization & Agents"
Cohesion: 0.09
Nodes (8): BaseAgent, HierarchicalGA, Remove services that cover zero demand corridors or have a         clearly nega, HubMILP, Enumerate (s1, s2, hub) pairs where services share a hub port.         Prioriti, Keep services covering demand corridors with positive margin., RegionalAgent, ServiceGeneratorAgent

### Community 4 - "Evaluation & Orchestration"
Cohesion: 0.09
Nodes (10): LLMEvaluator, _is_valid_analysis(), _is_valid_summary(), OrchestratorAgent, Apply coordinator's gradient feedback to the Problem object so the         next, PortClustering, regional_splitter.py — Fixed v2 ================================ KEY FIX: Each, Build a regional sub-problem.          Demand rule (NO DUPLICATION): (+2 more)

### Community 5 - "Test Utilities & Reporting"
Cohesion: 0.28
Nodes (27): assert_contains(), assert_ge(), assert_gt(), assert_has_number(), assert_range(), assert_true(), fail(), hdr() (+19 more)

### Community 6 - "Service & Network Loading"
Cohesion: 0.16
Nodes (3): CandidateServiceGenerator, NetworkLoader, Test Candidate Service Generator

### Community 7 - "Step Validation"
Cohesion: 0.33
Nodes (1): Step1Validator

### Community 8 - "Service GA Operations"
Cohesion: 0.25
Nodes (3): _crossover(), Bias initial population toward high-demand services so the GA         starts fr, Objective = w1·Profit + w2·Coverage − w3·Cost          Profit = Revenue − Oper

### Community 9 - "Quality & Verification"
Cohesion: 0.33
Nodes (6): Test Agent, Verification Before Completion, No Behavior Change Principle, pytest (7.4.4), Output Consistency Validation, 100% Output Accuracy After Optimization

### Community 10 - "GA Controls Testing"
Cohesion: 0.7
Nodes (4): create_larger_test_problem(), run_comprehensive_test(), test_frequency_ga_with_controls(), test_service_ga_with_controls()

### Community 11 - "GA Controls Validation"
Cohesion: 0.8
Nodes (4): create_test_problem(), test_frequency_ga(), test_service_ga(), validate_ga_controls()

### Community 12 - "LLM Metrics"
Cohesion: 0.4
Nodes (1): LLMMetrics

### Community 13 - "Frequency GA Analysis"
Cohesion: 0.4
Nodes (2): For each active service, sum the weekly TEU of demands where         BOTH origi, optimal_freq_i = clamp( ceil( route_demand_i / capacity_i ), 1, max_freq )

### Community 14 - "Frequency GA Evaluation"
Cohesion: 0.4
Nodes (2): Start near the analytical solution and jitter by ±1., fitness = revenue − operating_cost − overcapacity_penalty          revenue = Σ

### Community 15 - "Hub Detection Scoring"
Cohesion: 0.4
Nodes (2): Compute demand-based importance score for each port.          PERFORMANCE OPTI, Count number of connections for each port.

### Community 16 - "Graph Construction"
Cohesion: 0.5
Nodes (0): 

### Community 17 - "Flow Optimization"
Cohesion: 0.5
Nodes (1): FlowOptimizer

### Community 18 - "Service GA Initialization"
Cohesion: 0.5
Nodes (1): For each service, record the sum of weekly TEU for OD pairs         that are di

### Community 19 - "CLAUDE System Principles"
Cohesion: 0.5
Nodes (4): Debugging Agent, Execution Principle: Understand-Plan-Execute-Verify-Store, Memory First Principle, Self-Improvement Loop

### Community 20 - "Data Preprocessing"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Sample Data Utilities"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "GA Unit Tests"
Cohesion: 0.67
Nodes (1): Test all Genetic Algorithms (ServiceGA, FrequencyGA, HierarchicalGA)

### Community 23 - "LLM Tests"
Cohesion: 0.67
Nodes (0): 

### Community 24 - "MILP Tests"
Cohesion: 0.67
Nodes (1): Test Hub MILP optimizer (supports transshipment version)

### Community 25 - "Regional Agent Tests"
Cohesion: 1.0
Nodes (2): load_problem(), test_regional_agent()

### Community 26 - "Web API Stack"
Cohesion: 0.67
Nodes (3): fastapi (0.109.0), pydantic (2.5.3), uvicorn (0.27.0)

### Community 27 - "Logging"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Clustering Tests"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Data Loader Tests"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "ML Dependencies"
Cohesion: 1.0
Nodes (2): gymnasium (0.29.1), torch (2.1.0)

### Community 31 - "Source Init"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Agents Init"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Evaluator Manager"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "LLM Init"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Optimization Init"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Optimization Pipeline"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Pipeline Orchestration"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Utils Init"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Tests Init"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Architect Agent"
Cohesion: 1.0
Nodes (1): Architect Agent

### Community 41 - "Reviewer Agent"
Cohesion: 1.0
Nodes (1): Reviewer Agent

### Community 42 - "Future: Parallel Eval"
Cohesion: 1.0
Nodes (1): Future: Parallel Population Evaluation

### Community 43 - "Future: Adaptive Population"
Cohesion: 1.0
Nodes (1): Future: Adaptive Population Sizing

### Community 44 - "Runtime Reduction"
Cohesion: 1.0
Nodes (1): 25-35% Overall Runtime Reduction

### Community 45 - "Environment Config"
Cohesion: 1.0
Nodes (1): python-dotenv (1.0.0)

### Community 46 - "Threshold Configuration"
Cohesion: 1.0
Nodes (1): 60% Reduction in Early Stop Threshold

## Knowledge Gaps
- **59 isolated node(s):** `Base Agent class - parent for all agents`, `regional_splitter.py — Fixed v2 ================================ KEY FIX: Each`, `Build a regional sub-problem.          Demand rule (NO DUPLICATION):`, `Split the global problem into one sub-problem per cluster.          Demand par`, `For each active service, sum the weekly TEU of demands where         BOTH origi` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Logging`** (2 nodes): `setup_logging()`, `logger.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Clustering Tests`** (2 nodes): `test_clustering()`, `test_clustering.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Data Loader Tests`** (2 nodes): `test_data_loader()`, `test_data_loader.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `ML Dependencies`** (2 nodes): `gymnasium (0.29.1)`, `torch (2.1.0)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Source Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Agents Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Evaluator Manager`** (1 nodes): `evaluator_manager.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `LLM Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Optimization Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Optimization Pipeline`** (1 nodes): `optimization_pipeline.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pipeline Orchestration`** (1 nodes): `orchestration.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Utils Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tests Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Architect Agent`** (1 nodes): `Architect Agent`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Reviewer Agent`** (1 nodes): `Reviewer Agent`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Future: Parallel Eval`** (1 nodes): `Future: Parallel Population Evaluation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Future: Adaptive Population`** (1 nodes): `Future: Adaptive Population Sizing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Runtime Reduction`** (1 nodes): `25-35% Overall Runtime Reduction`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Environment Config`** (1 nodes): `python-dotenv (1.0.0)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Threshold Configuration`** (1 nodes): `60% Reduction in Early Stop Threshold`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OrchestratorAgent` connect `Evaluation & Orchestration` to `GA Optimization & Benchmarking`, `Agent & LLM Infrastructure`, `Hierarchical Optimization & Agents`, `Step Validation`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `Problem` connect `GA Optimization & Benchmarking` to `Hierarchical Optimization & Agents`, `Evaluation & Orchestration`, `Service & Network Loading`, `Step Validation`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `RegionalAgent` connect `Hierarchical Optimization & Agents` to `GA Optimization & Benchmarking`, `Agent & LLM Infrastructure`, `Evaluation & Orchestration`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `Problem` (e.g. with `Benchmark script to demonstrate performance improvements before and after optimi` and `Create a test problem of specified size.`) actually correct?**
  _`Problem` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 38 inferred relationships involving `Service` (e.g. with `Benchmark script to demonstrate performance improvements before and after optimi` and `Create a test problem of specified size.`) actually correct?**
  _`Service` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `Port` (e.g. with `Benchmark script to demonstrate performance improvements before and after optimi` and `Create a test problem of specified size.`) actually correct?**
  _`Port` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `Demand` (e.g. with `Benchmark script to demonstrate performance improvements before and after optimi` and `Create a test problem of specified size.`) actually correct?**
  _`Demand` has 36 INFERRED edges - model-reasoned connections that need verification._