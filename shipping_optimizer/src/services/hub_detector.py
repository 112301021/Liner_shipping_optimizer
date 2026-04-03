import numpy as np
from collections import defaultdict


class HubDetector:

    def __init__(self, problem):
        self.problem = problem

    def compute_demand_scores(self):
        """
        Compute demand-based importance score for each port.
        """
        scores = defaultdict(float)

        for d in self.problem.demands:
            scores[d.origin] += d.weekly_teu
            scores[d.destination] += d.weekly_teu

        return scores

    def compute_connectivity_scores(self):
        """
        Count number of connections for each port.
        """
        connections = defaultdict(int)

        for d in self.problem.demands:
            connections[d.origin] += 1
            connections[d.destination] += 1

        return connections

    def detect_hubs(self, top_k=10):
        """
        Identify hub ports.
        """
        demand_scores = self.compute_demand_scores()
        conn_scores = self.compute_connectivity_scores()

        hub_scores = {}

        for p in self.problem.ports:
            pid = p.id

            demand = demand_scores.get(pid, 0)
            conn = conn_scores.get(pid, 0)

            hub_scores[pid] = demand * 0.7 + conn * 0.3

        hubs = sorted(
            hub_scores,
            key=hub_scores.get,
            reverse=True
        )[:top_k]

        return hubs

    def hub_summary(self, hubs):

        summary = []

        for h in hubs:

            p = self.problem.ports[h]

            summary.append({
                "id": h,
                "name": p.name,
                "lat": p.latitude,
                "lon": p.longitude
            })

        return summary