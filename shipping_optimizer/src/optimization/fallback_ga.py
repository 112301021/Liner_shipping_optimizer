import numpy as np
import random
from typing import Optional

from src.optimization.data import Problem
from src.optimization.hub_milp import HubMILP
from src.optimization.fallback_ga import Chromosome
from src.utils.logger import logger


class FallbackGA:
    """
    Fast fallback GA with RL warm-start support

    - Single-stage GA (services + frequencies)
    - Warm-start from RL solution
    - Early convergence (low latency)
    """

    def __init__(
        self,
        problem: Problem,
        population_size: int = 30,
        generations: int = 20,
        mutation_rate: float = 0.1,
        elite_size: int = 4
    ):
        self.problem = problem
        self.num_services = len(problem.services)

        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size

    # ------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------
    def solve(self, warm_start: Optional[Chromosome] = None) -> Chromosome:

        population = self._initialize_population(warm_start)

        best = None
        best_fitness = -1e9

        for gen in range(self.generations):

            fitness_scores = [self._fitness(ind) for ind in population]

            # Track best
            for i, f in enumerate(fitness_scores):
                if f > best_fitness:
                    best_fitness = f
                    best = population[i]

            # Selection
            selected = self._select(population, fitness_scores)

            # Crossover + Mutation
            new_population = self._reproduce(selected)

            # Elitism
            elites = self._get_elites(population, fitness_scores)
            population = elites + new_population[:self.population_size - self.elite_size]

        logger.info(
            "fallback_ga_complete",
            best_fitness=best_fitness,
            services=sum(best.services)
        )

        return best

    # ------------------------------------------------
    # INITIALIZATION (WITH RL WARM START)
    # ------------------------------------------------
    def _initialize_population(self, warm_start):

        population = []

        # 🔥 Inject RL solution directly
        if warm_start is not None:
            population.append(warm_start)

        while len(population) < self.population_size:

            services = np.random.randint(0, 2, self.num_services).tolist()

            # Ensure at least 1 service
            if sum(services) == 0:
                services[random.randint(0, self.num_services - 1)] = 1

            frequencies = [random.randint(1, 3) if s == 1 else 0 for s in services]

            population.append(Chromosome(services, frequencies))

        return population

    # ------------------------------------------------
    # FITNESS (MILP-BASED)
    # ------------------------------------------------
    def _fitness(self, chromosome: Chromosome):

        milp = HubMILP(self.problem, chromosome)
        result = milp.solve()

        profit = result.get("profit", 0)

        # Penalize too many services (important)
        penalty = sum(chromosome.services) * 1000

        return profit - penalty

    # ------------------------------------------------
    # SELECTION
    # ------------------------------------------------
    def _select(self, population, fitness):

        probs = np.array(fitness) - min(fitness) + 1e-6
        probs = probs / probs.sum()

        indices = np.random.choice(
            len(population),
            size=len(population),
            p=probs
        )

        return [population[i] for i in indices]

    # ------------------------------------------------
    # CROSSOVER + MUTATION
    # ------------------------------------------------
    def _reproduce(self, selected):

        new_population = []

        for i in range(0, len(selected), 2):

            p1 = selected[i]
            p2 = selected[(i + 1) % len(selected)]

            child1, child2 = self._crossover(p1, p2)

            self._mutate(child1)
            self._mutate(child2)

            new_population.extend([child1, child2])

        return new_population

    def _crossover(self, p1: Chromosome, p2: Chromosome):

        point = random.randint(1, self.num_services - 1)

        s1 = p1.services[:point] + p2.services[point:]
        s2 = p2.services[:point] + p1.services[point:]

        f1 = p1.frequencies[:point] + p2.frequencies[point:]
        f2 = p2.frequencies[:point] + p1.frequencies[point:]

        return Chromosome(s1, f1), Chromosome(s2, f2)

    def _mutate(self, chromosome: Chromosome):

        for i in range(self.num_services):

            if random.random() < self.mutation_rate:
                chromosome.services[i] = 1 - chromosome.services[i]

                if chromosome.services[i] == 1:
                    chromosome.frequencies[i] = random.randint(1, 3)
                else:
                    chromosome.frequencies[i] = 0

    # ------------------------------------------------
    # ELITISM
    # ------------------------------------------------
    def _get_elites(self, population, fitness):

        sorted_idx = np.argsort(fitness)[::-1]
        return [population[i] for i in sorted_idx[:self.elite_size]]