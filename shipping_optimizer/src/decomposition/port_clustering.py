import numpy as np
from sklearn.cluster import KMeans

class PortClustering:


    def __init__(self, n_clusters=None, random_state=42):

        self.n_clusters = n_clusters
        self.random_state = random_state

    # --------------------------------
    # Adaptive cluster count
    # --------------------------------
    def compute_cluster_count(self, ports):

        n = len(ports)

        # sqrt heuristic
        k = int(np.sqrt(n))

        return max(3, min(k, 25))

    # --------------------------------
    # Cluster ports
    # --------------------------------
    def cluster_ports(self, ports):

        coords = []
        valid_ports = []

        for p in ports:
            if p.latitude is None or p.longitude is None:
                continue

            if np.isnan(p.latitude) or np.isnan(p.longitude):
                continue

            coords.append([p.latitude, p.longitude])
            valid_ports.append(p)

        coords = np.array(coords)

        # use manual cluster count if provided
        if self.n_clusters is not None:
            n_clusters = self.n_clusters
        else:
            n_clusters = self.compute_cluster_count(ports)

        model = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=20
        )

        labels = model.fit_predict(coords)

        clusters = {}

        for i, label in enumerate(labels):
            clusters.setdefault(label, [])
            clusters[label].append(valid_ports[i].id)

        return clusters

    # --------------------------------
    # Cluster summary
    # --------------------------------
    def cluster_summary(self, clusters, ports):

        port_lookup = {p.id: p for p in ports}

        summary = {}

        for cid, port_ids in clusters.items():

            names = [
                port_lookup[p].name
                for p in port_ids[:5]
                if p in port_lookup
            ]

            summary[cid] = {
                "num_ports": len(port_ids),
                "sample_ports": names
            }

        return summary