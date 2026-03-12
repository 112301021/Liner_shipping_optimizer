import random
import numpy as np


class ServiceGA:

    def __init__(self, problem, pop_size=80, generations=120):

        self.problem = problem
        self.pop_size = pop_size
        self.generations = generations

        self.num_services = len(problem.services)

        self.total_demand = sum(
            d.weekly_teu for d in problem.demands
        )

        self.avg_revenue = np.mean(
            [d.revenue_per_teu for d in problem.demands]
        )

        self.max_services = max(5, int(0.1 * self.num_services))
        # --------------------------------
        # Precompute service-demand compatibility
        # --------------------------------

        self.service_demands = [[] for _ in range(self.num_services)]

        for i, svc in enumerate(self.problem.services):

            svc_ports = set(svc.ports)

            for j, d in enumerate(self.problem.demands):

                if d.origin in svc_ports or d.destination in svc_ports:
                    self.service_demands[i].append(j)

    def random_solution(self):

        services = [0]*self.num_services

        selected = random.sample(
            range(self.num_services),
            random.randint(5, self.max_services)
        )

        for s in selected:
            services[s] = 1

        return services

    def evaluate(self, services):

    
        selected_services = [
            self.problem.services[i]
            for i, s in enumerate(services)
            if s == 1
        ]

        if len(selected_services) == 0:
            return -1e12

        # ------------------------------
        # Service capacity
        # ------------------------------

        total_capacity = sum(
            svc.capacity
            for svc in selected_services
        )

        # ------------------------------
        # Cargo flow allocation
        # ------------------------------
        revenue = 0

        service_capacity = {
            i: svc.capacity
            for i, svc in enumerate(selected_services)
        }

        for svc_idx, svc in enumerate(selected_services):

            capacity_left = service_capacity[svc_idx]

            if capacity_left <= 0:
                continue

            service_id = self.problem.services.index(svc)
            demand_ids = self.service_demands[service_id]

            for d_id in demand_ids:

                d = self.problem.demands[d_id]

                alloc = min(capacity_left, d.weekly_teu)

                if alloc <= 0:
                    continue

                revenue += alloc * d.revenue_per_teu
                capacity_left -= alloc

                if capacity_left <= 0:
                    break
                
        # ------------------------------
        # Service operating cost
        # ------------------------------

        service_cost = sum(
            svc.weekly_cost
            for svc in selected_services
        )

        # ------------------------------
        # Port handling cost
        # ------------------------------

        handling_cost = 80   # $/TEU example

        port_calls = sum(
            len(svc.ports)
            for svc in selected_services
        )

        port_cost = port_calls * handling_cost 

        # ------------------------------
        # Fleet size constraint
        # ------------------------------

        required_vessels = sum(
            max(1, int(svc.cycle_time / 7))
            for svc in selected_services
        )

        fleet_size = getattr(self.problem, "fleet_size", 100)

        penalty = 0

        if required_vessels > fleet_size:
            penalty = (required_vessels - fleet_size) * 20000
            

        # ------------------------------
        # Service count penalty
        # ------------------------------
        num_services = len(selected_services)
        penalty_services = (num_services) * 20000
        
        # ------------------------------
        # Final profit
        # ------------------------------

        profit = (revenue - service_cost - port_cost - penalty-penalty_services)

        return profit
        


    def crossover(self, p1, p2):

        point = random.randint(1, self.num_services-2)

        child = p1[:point] + p2[point:]

        return child

    def mutate(self, sol):

        idx = random.randint(0, self.num_services-1)

        sol[idx] = 1 - sol[idx]

        return sol

    def run(self):

        population = [
            self.random_solution()
            for _ in range(self.pop_size)
        ]

        fitness = [
            self.evaluate(p)
            for p in population
        ]

        for _ in range(self.generations):

            ranked = sorted(
                zip(population, fitness),
                key=lambda x: x[1],
                reverse=True
            )

            population = [x[0] for x in ranked[:10]]

            while len(population) < self.pop_size:

                p1 = random.choice(ranked[:20])[0]
                p2 = random.choice(ranked[:20])[0]

                child = self.crossover(p1, p2)

                if random.random() < 0.2:
                    child = self.mutate(child)

                population.append(child)

            fitness = [
                self.evaluate(p)
                for p in population
            ]

        best = population[np.argmax(fitness)]

        return best