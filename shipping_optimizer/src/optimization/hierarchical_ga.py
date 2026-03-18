import numpy as np

from src.optimization.service_ga import ServiceGA
from src.optimization.frequency_ga import FrequencyGA


class HierarchicalGA:

    def __init__(self, problem):

        self.problem = problem

    def run(self):

        # ------------------------
        # Level 1: service selection
        # ------------------------

        service_ga = ServiceGA(self.problem)

        best_services = service_ga.run()

        # ------------------------
        # Level 2: frequency optimization
        # ------------------------

        freq_ga = FrequencyGA(self.problem, best_services)

        best_freq = freq_ga.run()

        chromosome = {
            "services": best_services,
            "frequencies": best_freq
        }

        return chromosome
