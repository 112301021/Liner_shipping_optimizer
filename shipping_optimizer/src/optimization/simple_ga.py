import random
import numpy as np
from typing import List
from src.optimization.data import Problem
from src.utils.config import Config
from src.utils.logger import logger 

class Chromosome:
    def __init__(self, services:List[int], frequencies: List[int]):
        self.services = services
        self.frequencies = frequencies
        self.fitness = 0.0
        
    def __repr__(self):
        n_selected = sum(self.services)
        return f"Chromosome(services={n_selected}, fitness= {self.fitness:.0f})"
    
class SimpleGA:
    def __init__(self, problem: Problem):
       
        self.problem = problem
        self.pop_size = Config.GA_POPULATION_SIZE
        self.generations = Config.GA_GENERATIONS
        
    def create_random(self) -> Chromosome:
        n = len(self.problem.servcies)
        services = [random.randint(0,1) for _ in range(n)]
        while sum(services) < 3:
            services[random.randint(0,n-1)] = 1
            
        frequencies = [
            random.choice([1,2,3]) if services[i] == 1 else 0
            for i in range(n)
        ]
        return Chromosome(services, frequencies)
    
    def evaluate(self, chromo:Chromosome) -> float:
        total_capacity = sum(
            self.problem.services[i].capacity * chromo.frequencies[i]
            for i in range(len(chromo.services))
            if chromo.services[i] == 1
        )
        
        total_demand = sum(d.weekly_teu for d in self.problem.demands)
        satisfied = min(total_capacity, total_demand)
        avg_revenue = np.mean([d.revenue_per_teu for d in self.problem.demands])
        revenue = satisfied * avg_revenue
        
        cost = sum(
            self.problem.services[i].weekly_cost * chromo.frequencies[i]
            for i in range(len(chromo.services))
            if chromo.services[i] == 1
        )
        
        profit = revenue - cost 
        
        n_services = sum(chromo.services)
        penalty = n_services * 10000
        
        return profit - penalty
    

    def crossover(self, p1:Chromosome, p2:Chromosome) -> Chromosome:
        point = random.randint(1, len(p1.services) - 1)
        services = p1.services[:point] + p2.services[point:]
        frequencies = p1.frequencies[:point] + p2.frequencies[point:]
        
        return Chromosome(services, frequencies)
    
    def mutate(self, chromo:Chromosome) -> Chromosome:
        services = chromo.services.copy()
        frequencies = chromo.frequencies.copy()
        #flip a random service
        idx = random.randint(0, len(services) - 1)
        services[idx] = 1- services[idx]
        if services[idx] == 1:
            frequencies[idx] = random.choice([1,2,3])
        else:
            frequencies[idx] = 0
        
        return Chromosome(services, frequencies)
    
    def run(self) -> Chromosome:
        logger.info("ga_started", 
                    population=self.pop_size,
                    generations = self.generations)
        
        population = [self.create_random() for _ in range(self.pop_size)]
        #Evaluate
        for chromo in population:
            chromo.fitness = self.evaluate(chromo)
        
        #Evolution
        for gen in range(self.generations):
            population.sort(key=lambda x: x.fitness, reverse=True)
            if gen % 10 == 0:
                best = population[0]
                logger.info("ga_progress",
                            generations = gen,
                            best_fitness=best.fitness,
                            services = sum(best.services))
                
            elite_size = self.pop_size // 5
            new_pop = population[:elite_size]
            
            #create offspring
            while len(new_pop) < self.pop_size:
                #tournament selection
                p1 = max(random.sample(population, 3), key=lambda x: x.fitness)
                p2 = max(random.sample(population, 3), key=lambda x:x.fitness)
                #crossover
                child = self.crossover(p1,p2)
                #mutate
                if random.random() < 0.1:
                    child = self.mutate(child)
                #Evaluate
                child.fitness = self.evaluate(child)
                
                new_pop.append(child)
            population = new_pop
        
        #return best solution
        best = max(population, key=lambda x: x.fitness)
        logger.info("ga_complete",
                    best_fitness = best.fitness,
                    services_selected = sum(best.services))
        return best    
            
    
    
    
    