import random
import numpy as np
from typing import List

from src.optimization.data import Problem
from src.utils.config import Config
from src.utils.logger import logger


class Chromosome:

    def __init__(self, services: List[int], frequencies: List[int]):
        self.services = services
        self.frequencies = frequencies
        self.fitness = 0.0

    def __repr__(self):
        return f"Chromosome(services={sum(self.services)}, fitness={self.fitness:.0f})"


class SimpleGA:

    def __init__(self, problem: Problem):

        self.problem = problem
        self.pop_size = Config.GA_POPULATION_SIZE
        self.generations = Config.GA_GENERATIONS
        self.num_services = len(problem.services)

        # precompute values for speed
        self.service_capacity = np.array([s.capacity for s in problem.services])
        self.service_cost = np.array([s.weekly_cost for s in problem.services])

        self.total_demand = sum(d.weekly_teu for d in problem.demands)
        self.avg_revenue = np.mean([d.revenue_per_teu for d in problem.demands])

    # -----------------------------
    # Create random chromosome
    # -----------------------------
    def create_random(self) -> Chromosome:

        services = [random.randint(0, 1) for _ in range(self.num_services)]

        while sum(services) < 5:
            services[random.randint(0, self.num_services - 1)] = 1

        frequencies = [
            random.choice([1, 2, 3]) if services[i] == 1 else 0
            for i in range(self.num_services)
        ]

        chromo = Chromosome(services, frequencies)
        return self.repair(chromo)

    # -----------------------------
    # Repair chromosome
    # -----------------------------
    def repair(self, chromo: Chromosome):

        if sum(chromo.services) == 0:

            idx = random.randint(0, self.num_services - 1)
            chromo.services[idx] = 1
            chromo.frequencies[idx] = 1

        for i in range(self.num_services):

            if chromo.services[i] == 0:
                chromo.frequencies[i] = 0

            if chromo.services[i] == 1 and chromo.frequencies[i] == 0:
                chromo.frequencies[i] = 1

        return chromo

    # -----------------------------
    # Fitness evaluation
    # -----------------------------
    def evaluate(self, chromo: Chromosome) -> float:

        services = np.array(chromo.services)
        freqs = np.array(chromo.frequencies)

        capacity = np.sum(self.service_capacity * freqs * services)
        cost = np.sum(self.service_cost * freqs * services)

        satisfied = min(capacity, self.total_demand)

        revenue = satisfied * self.avg_revenue

        profit = revenue - cost

        # penalties
        service_penalty = sum(chromo.services) * 6000

        oversupply = max(0, capacity - self.total_demand)
        oversupply_penalty = oversupply * 0.05

        fitness = profit - service_penalty - oversupply_penalty

        return fitness

    # -----------------------------
    # Crossover
    # -----------------------------
    def crossover(self, p1: Chromosome, p2: Chromosome) -> Chromosome:

        point = random.randint(1, self.num_services - 2)

        services = p1.services[:point] + p2.services[point:]
        freqs = p1.frequencies[:point] + p2.frequencies[point:]

        child = Chromosome(services, freqs)

        return self.repair(child)

    # -----------------------------
    # Mutation
    # -----------------------------
    def mutate(self, chromo: Chromosome) -> Chromosome:

        services = chromo.services.copy()
        freqs = chromo.frequencies.copy()

        idx = random.randint(0, self.num_services - 1)

        if random.random() < 0.5:

            services[idx] = 1 - services[idx]

            if services[idx] == 1:
                freqs[idx] = random.choice([1, 2, 3])
            else:
                freqs[idx] = 0

        else:

            if services[idx] == 1:
                freqs[idx] = random.choice([1, 2, 3])

        return self.repair(Chromosome(services, freqs))

    # -----------------------------
    # Run GA
    # -----------------------------
    def run(self) -> Chromosome:

        logger.info(
            "ga_started",
            population=self.pop_size,
            generations=self.generations
        )

        population = [self.create_random() for _ in range(self.pop_size)]

        for c in population:
            c.fitness = self.evaluate(c)

        best_global = None

        for gen in range(self.generations):

            population.sort(key=lambda x: x.fitness, reverse=True)

            best = population[0]

            if best_global is None or best.fitness > best_global.fitness:
                best_global = best

            if gen % 10 == 0:

                logger.info(
                    "ga_progress",
                    generation=gen,
                    best_fitness=best.fitness,
                    services=sum(best.services)
                )

            elite_size = max(2, self.pop_size // 5)

            new_pop = population[:elite_size]

            while len(new_pop) < self.pop_size:

                p1 = max(random.sample(population, 4), key=lambda x: x.fitness)
                p2 = max(random.sample(population, 4), key=lambda x: x.fitness)

                child = self.crossover(p1, p2)

                if random.random() < 0.2:
                    child = self.mutate(child)

                child.fitness = self.evaluate(child)

                new_pop.append(child)

            population = new_pop

        best = max(population, key=lambda x: x.fitness)

        logger.info(
            "ga_complete",
            best_fitness=best.fitness,
            services_selected=sum(best.services)
        )

        return best