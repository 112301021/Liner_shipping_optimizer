from collections import defaultdict
import random


class CandidateServiceGenerator:

    def __init__(self, problem):

        self.problem = problem


    # ------------------------------------------------
    # Find high-demand corridors
    # ------------------------------------------------
    def find_demand_corridors(self, top_k=100):

        corridor_demand = defaultdict(float)

        for d in self.problem.demands:

            key = (d.origin, d.destination)
            corridor_demand[key] += d.weekly_teu

        corridors = sorted(
            corridor_demand.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [c[0] for c in corridors[:top_k]]


    # ------------------------------------------------
    # Generate services along corridors
    # ------------------------------------------------
    def generate_corridor_services(self, corridors):

        services = []

        for origin, destination in corridors:

            route = [origin]

            # optional hub insertion
            if random.random() < 0.6:

                hub = random.choice(list(self.problem.distance_matrix.keys()))
                route.append(hub)

            route.append(destination)

            services.append({
                "ports": route
            })

        return services


    # ------------------------------------------------
    # Add regional feeder services
    # ------------------------------------------------
    def generate_feeders(self, hubs, num=100):

        services = []

        ports = [p.id for p in self.problem.ports]

        for _ in range(num):

            hub = random.choice(hubs)

            spoke = random.choice(ports)

            if hub == spoke:
                continue

            services.append({
                "ports": [hub, spoke]
            })

        return services


    # ------------------------------------------------
    # Main generation function
    # ------------------------------------------------
    def generate_services(self, num_services=400):

        corridors = self.find_demand_corridors(150)

        corridor_services = self.generate_corridor_services(corridors)

        # detect hubs (top demand ports)
        port_demand = defaultdict(float)

        for d in self.problem.demands:
            port_demand[d.origin] += d.weekly_teu
            port_demand[d.destination] += d.weekly_teu

        hubs = sorted(
            port_demand,
            key=port_demand.get,
            reverse=True
        )[:10]

        feeder_services = self.generate_feeders(hubs, 150)

        all_services = corridor_services + feeder_services

        return all_services[:num_services] 