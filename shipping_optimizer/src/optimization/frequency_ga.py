import random


class FrequencyGA:

    def __init__(self, problem, services):

        self.problem = problem
        self.services = services
        self.num_services = len(services)

    def random_freq(self):

        freq = []

        for s in self.services:

            if s:
                freq.append(random.randint(1,3))
            else:
                freq.append(0)

        return freq

    def evaluate(self, freq):

        capacity = 0
        cost = 0

        for i, f in enumerate(freq):

            if f:

                svc = self.problem.services[i]

                capacity += svc.capacity * f
                cost += svc.weekly_cost * f

        demand = sum(d.weekly_teu for d in self.problem.demands)

        satisfied = min(capacity, demand)

        revenue = satisfied * 1000

        return revenue - cost

    def run(self):

        population = [self.random_freq() for _ in range(40)]

        fitness = [self.evaluate(p) for p in population]

        for _ in range(50):

            ranked = sorted(
                zip(population, fitness),
                key=lambda x: x[1],
                reverse=True
            )

            population = [x[0] for x in ranked[:10]]

            while len(population) < 40:

                p1 = random.choice(population)
                child = p1.copy()

                idx = random.randint(0,self.num_services-1)

                if child[idx] > 0:
                    child[idx] = random.randint(1,3)

                population.append(child)

            fitness = [self.evaluate(p) for p in population]

        return population[fitness.index(max(fitness))]