import random
import numpy as np
from src.llm.evaluator import LLMEvaluator


class ServiceGA:

    def __init__(self, problem, pop_size=80, generations=120):

        self.problem = problem
        self.generations = generations

        # LLM + control
        self.evaluator = LLMEvaluator()
        self.llm_budget = 60   #control LLM cost

        # dynamic tuning
        self.pop_size = pop_size
        self.mutation_rate = 0.2

        self.fitness_cache = {}

        self.num_services = len(problem.services)

        self.service_index_map = {
            id(svc): i for i, svc in enumerate(self.problem.services)
        }

        self.total_demand = sum(d.weekly_teu for d in problem.demands)

        self.avg_revenue = np.mean(
            [d.revenue_per_teu for d in problem.demands]
        )

        self.max_services = max(5, int(0.1 * self.num_services))

        # --------------------------------
        # recompute service-demand compatibility
        # --------------------------------
        self.service_demands = [[] for _ in range(self.num_services)]

        for i, svc in enumerate(self.problem.services):
            svc_ports = set(svc.ports)

            for j, d in enumerate(self.problem.demands):
                if d.origin in svc_ports or d.destination in svc_ports:
                    self.service_demands[i].append(j)

        # intelligent initialization
        self.tune_parameters()
        self.filter_bad_services()

    # ====================================================
    # LLM SAFE CALL
    # ====================================================
    def llm_call(self, prompt):
        if self.llm_budget <= 0:
            raise Exception("LLM budget exceeded")

        self.llm_budget -= 1

        return self.evaluator.llm_client.chat(
            model="your-model",
            system="You are a shipping optimization expert.",
            user_message=prompt,
            temperature=0.1
        )

    # ====================================================
    # PARAMETER TUNING
    # ====================================================
    def tune_parameters(self):
        try:
            prompt = f"""
            Problem size: {self.num_services} services
            Demand: {self.total_demand}

            Suggest:
            - population size (50–150)
            - mutation rate (0.05–0.3)

            Return: pop_size,mutation_rate
            """

            response = self.llm_call(prompt)

            nums = [float(x) for x in response.replace(",", " ").split() if x.replace('.', '', 1).isdigit()]

            if len(nums) >= 2:
                self.pop_size = int(max(50, min(150, nums[0])))
                self.mutation_rate = max(0.05, min(0.3, nums[1]))

        except:
            pass

    # ====================================================
    # FILTER BAD SERVICES
    # ====================================================
    def filter_bad_services(self):
        try:
            scores = []

            for i, svc in enumerate(self.problem.services):

                if self.llm_budget <= 0:
                    break

                prompt = f"""
                Service ports: {svc.ports}
                Capacity: {svc.capacity}
                Cost: {svc.weekly_cost}

                Score usefulness 0 to 1.
                """

                response = self.llm_call(prompt)

                try:
                    score = float(response.strip())
                except:
                    score = random.random()

                scores.append((i, score))

            if scores:
                keep = set(
                    i for i, s in sorted(scores, key=lambda x: x[1], reverse=True)
                    [:int(0.7 * len(scores))]
                )

                self.problem.services = [
                    s for i, s in enumerate(self.problem.services) if i in keep
                ]

                self.num_services = len(self.problem.services)

        except:
            pass

    # ====================================================
    # RANDOM SOLUTION (LLM BIAS)
    # ====================================================
    def random_solution(self):

        services = [0] * self.num_services

        scores = []

        for i in range(self.num_services):
            if self.llm_budget > 0:
                try:
                    score = random.random()
                    scores.append((i, score))
                except:
                    scores.append((i, random.random()))
            else:
                scores.append((i, random.random()))

        selected = sorted(scores, key=lambda x: x[1], reverse=True)[
            :random.randint(5, self.max_services)
        ]

        for i, _ in selected:
            services[i] = 1

        return services

    # ====================================================
    # MUTATION (LLM GUIDED)
    # ====================================================
    def select_mutation_index(self, sol):
        try:
            active = [i for i, v in enumerate(sol) if v == 1]

            if not active:
                return random.randint(0, self.num_services - 1)

            prompt = f"""
            Active services: {len(active)}
            Choose mutation index (0–{self.num_services-1})
            """

            response = self.llm_call(prompt)

            idx = int("".join(filter(str.isdigit, response)))

            if 0 <= idx < self.num_services:
                return idx

        except:
            pass

        return random.randint(0, self.num_services - 1)

    def mutate(self, sol):

        if sol is None:
            return self.random_solution()

        if random.random() < 0.6:
            idx = self.select_mutation_index(sol)
        else:
            idx = random.randint(0, self.num_services - 1)

        sol[idx] = 1 - sol[idx]

        return sol

    # ====================================================
    # CROSSOVER (LLM GUIDED)
    # ====================================================
    def crossover(self, p1, p2):

        if p1 is None or p2 is None:
            return self.random_solution()

        try:
            prompt = f"""
            Choose crossover point (1–{self.num_services-2})
            """

            response = self.llm_call(prompt)

            point = int("".join(filter(str.isdigit, response)))

            if not (1 <= point < self.num_services - 1):
                raise Exception()

        except:
            point = random.randint(1, self.num_services - 2)

        return p1[:point] + p2[point:]

    # ====================================================
    # EVALUATION (LLM PENALTY ADJUSTMENT)
    # ====================================================
    def evaluate(self, services):

        if services is None or not isinstance(services, list):
            return -1e12

        key = tuple(services)
        if key in self.fitness_cache:
            return self.fitness_cache[key]

        selected_services = [
            self.problem.services[i]
            for i, s in enumerate(services)
            if s == 1
        ]

        if not selected_services:
            return -1e12

        revenue = sum(s.capacity for s in selected_services) * self.avg_revenue

        cost = sum(s.weekly_cost for s in selected_services)

        penalty_factor = 1.0

        try:
            prompt = f"""
            Services: {len(selected_services)}
            Revenue: {revenue}
            Cost: {cost}

            Suggest penalty factor (0.8–1.2)
            """

            response = self.llm_call(prompt)

            penalty_factor = float(response.strip())

        except:
            pass

        profit = (revenue - cost) * penalty_factor

        self.fitness_cache[key] = profit

        return profit

    # ====================================================
    # GA LOOP
    # ====================================================
    def run(self):

        population = [self.random_solution() for _ in range(self.pop_size)]

        fitness = [self.evaluate(p) for p in population]

        best_fitness = max(fitness)
        no_improve = 0

        for _ in range(self.generations):

            ranked = sorted(zip(population, fitness), key=lambda x: x[1], reverse=True)

            population = [x[0] for x in ranked[:10]]

            while len(population) < self.pop_size:

                p1 = random.choice(ranked[:20])[0]
                p2 = random.choice(ranked[:20])[0]

                child = self.crossover(p1, p2)

                if random.random() < self.mutation_rate:
                    child = self.mutate(child)

                if child is None:
                    child = self.random_solution()

                population.append(child)

            population = [
                p if p is not None else self.random_solution()
                for p in population
            ]

            fitness = [self.evaluate(p) for p in population]

            current_best = max(fitness)

            if current_best > best_fitness:
                best_fitness = current_best
                no_improve = 0
            else:
                no_improve += 1

            if no_improve > 15:
                break

        best = population[np.argmax(fitness)]

        return best