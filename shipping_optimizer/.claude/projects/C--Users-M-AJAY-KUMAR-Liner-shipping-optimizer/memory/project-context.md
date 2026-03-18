# Liner Shipping Optimizer - Project Context

## Project Overview
A shipping optimization system using Genetic Algorithms (GA) for frequency planning, decomposition strategies for regional optimization, and agent-based workflows.

## Core Components

### 1. Optimization Engine (`src/optimization/`)
- **`frequency_ga.py`**: GA-based frequency optimization
- **`hierarchical_ga.py`**: Hierarchical/decomposition-based GA
- **`genetic_algorithm_base.py`**: Base GA class (if exists)
- **`objective_functions.py`**: Objective function implementations

### 2. Decomposition Layer (`src/decomposition/`)
- **`regional_splitter.py`**: Splits optimization into regional subproblems
- **`decomposition_strategies.py`**: Different decomposition approaches

### 3. Agents (`src/agents/`)
- Agent-based workflows for complex multi-step tasks
- Regional agents for domain-specific optimization

### 4. Testing (`tests/`)
- Unit tests for GA algorithms
- Tests for decomposition strategies
- Regional agent tests

## Key Technologies
- Genetic Algorithms (scipy.optimize)
- Python with NumPy
- Agent-based programming patterns

## Architecture Goals
- Decompose complex shipping optimization into manageable subproblems
- Use GA for efficient search in large solution spaces
- Modular design for extensibility
- Agent-based workflows for orchestration

## Memory Files
- `MEMORY.md`: Main memory index
- `architectural-review.md`: Architectural analysis and refactoring suggestions
- `project-context.md`: This file - project context and structure
