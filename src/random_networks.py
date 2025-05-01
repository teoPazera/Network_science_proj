import math
from multiprocessing import Pool
import random
import sqlite3
from geopy.distance import geodesic
import networkx as nx
import numpy as np
from src.util import graph_from_geojson, largest_connected_component


db_name = "src/random_networks_data/random_networks.sqlite"

def normalized_kirchhoff_index(G: nx.Graph) -> float:
    if not nx.is_connected(G):
        return float("inf")

    L = nx.laplacian_matrix(G, weight="distance").todense()
    eigenvalues = np.linalg.eigvalsh(L)

    eigenvalues = np.sort(eigenvalues)
    nonzero_eigenvalues = eigenvalues[1:]

    n = G.number_of_nodes()
    return (2 / (n - 1)) * np.sum(1.0 / nonzero_eigenvalues)


def connected_double_edge_swap_distance(G: nx.Graph, nswap: int) -> int:
        def edge_length(G, u, v):
            point_u = G.nodes[u]['geometry']
            point_v = G.nodes[v]['geometry']
            coords_u = point_u.coords[0]
            coords_v = point_v.coords[0]
            latlon_u = (coords_u[1], coords_u[0])
            latlon_v = (coords_v[1], coords_v[0])
            return geodesic(latlon_u, latlon_v).meters

        def is_almost_square(G, a, b, c, d, rel_tol):
            ab = G[a][b]["distance"]
            cd = G[c][d]["distance"]
            ad = edge_length(G, a, d)
            bc = edge_length(G, b, c)
            
            return (
                math.isclose(ab, cd, rel_tol=rel_tol) and
                math.isclose(ad, bc, rel_tol=rel_tol) and
                math.isclose(ab, ad, rel_tol=rel_tol)
            )

        def sample_almost_square(G, max_tries=1000, rel_tol=0.5):
            edges = list(G.edges())
            for _ in range(max_tries):
                (a, b), (c, d) = random.sample(edges, 2)
                if len({a, b, c, d}) < 4:
                    continue
                if is_almost_square(G, a, b, c, d, rel_tol):
                    return (a, b, c, d)
            return None
        
        swaps = 0
        for _ in range(nswap):
            square = sample_almost_square(G)
            if not square:
                continue

            a, b, c, d = square
            G_tmp = G.copy()
            G_tmp.remove_edge(a, b)
            G_tmp.remove_edge(c, d)
            G_tmp.add_edge(a, d)
            G_tmp.add_edge(b, c)

            if nx.is_connected(G_tmp):
                G.remove_edge(a, b)
                G.remove_edge(c, d)
                G.add_edge(a, d)
                G.add_edge(b, c)
            else:
                continue

            for u, v in zip([a, b], [d, c]):
                G[u][v]['distance'] = edge_length(G, u, v)

            swaps += 1
        return swaps


def generate_random_graphs(country, n = 200, nswap=100):
    G = largest_connected_component(graph_from_geojson(f"selected_fixed_graphs/{country}-railroad-network.json"))
    with sqlite3.connect(db_name) as conn:
        for i in range(n):
            print(country, f"{i+1}/{n}")
            H = G.copy()
            swaps = connected_double_edge_swap_distance(H, nswap=nswap)
            connected = nx.is_connected(H)
            k_H = normalized_kirchhoff_index(H)
            sum_distances = sum([d["distance"] for _, _, d in H.edges(data=True)])

            conn.execute(
                """
                INSERT INTO graphs(country, swaps, connected, kirchhoff, sum_distances)
                VALUES (?, ?, ?, ?, ?)
                """,
                (country, swaps, connected, k_H, sum_distances)
            )
            conn.commit()


def main() -> None:
    countries = ["svk"] * 5 + ["cze"] * 5
    with Pool(processes=10) as pool:
        pool.map(generate_random_graphs, countries)
  

if __name__ == "__main__":
    main()