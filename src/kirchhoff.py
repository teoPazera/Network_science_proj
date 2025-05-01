import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from src.util import graph_from_geojson, largest_connected_component, graph_to_folium
from shapely.geometry import shape, Point
import folium

def normalized_kirchhoff_index(G: nx.Graph) -> float:
    if not nx.is_connected(G):
        return float("inf")

    L = nx.laplacian_matrix(G, weight="distance").todense()
    eigenvalues = np.linalg.eigvalsh(L)

    eigenvalues = np.sort(eigenvalues)
    nonzero_eigenvalues = eigenvalues[eigenvalues != 0]

    n = G.number_of_nodes()
    return (2 / (n - 1)) * np.sum(1.0 / nonzero_eigenvalues)


def effective_edge_resistance_centrality(u, v, G, k_G) -> float:
    G_tmp = G.copy()
    G_tmp.remove_edge(u, v)
    k = normalized_kirchhoff_index(G_tmp) 
    if k == float("inf"):
        return float("inf")
    return (k - k_G) / k_G

def effective_vertex_resistance_centrality(n, G, k_G) -> float:
    G_tmp = G.copy()
    G_tmp.remove_node(n)
    k = normalized_kirchhoff_index(G_tmp) 
    if k == float("inf"):
        return float("inf")
    return (k - k_G) / k_G


def main() -> None:
    G_svk: nx.Graph = largest_connected_component(
        graph_from_geojson("selected_fixed_graphs/svk-railroad-network.json")
        )
    G_cze: nx.Graph = largest_connected_component(
        graph_from_geojson("selected_fixed_graphs/cze-railroad-network.json")
        )

    for G, c in zip([G_svk, G_cze], ["svk", "cze"]):
        print(c)
        k_G = normalized_kirchhoff_index(G)
        print(c, k_G)

        kirchhoff_indexes = {}
        kirchhoff_indexes_list = []
        for n in G.nodes():
            k = effective_vertex_resistance_centrality(n, G, k_G)
            if k == float("inf"):
                continue
            kirchhoff_indexes[(n)] = k
            kirchhoff_indexes_list.append(k)

        q = np.quantile(kirchhoff_indexes_list, 0.95)

        m = graph_to_folium(G, c)
        for node, data in G.nodes(data=True):
            if node not in kirchhoff_indexes or kirchhoff_indexes[node] < q:
                continue
            if 'geometry' in data and isinstance(data['geometry'], Point):
                folium.CircleMarker(
                    location=[data['geometry'].y, data['geometry'].x],
                    radius=3,
                    color='orange',
                    fill=True,
                    fill_color='orange',
                    fill_opacity=0.7
                ).add_to(m)
        print("cutoff", q)
        m.save(f"src/visualizations/resistance_{c}_vertex.html")


    for G, c in zip([G_svk, G_cze], ["svk", "cze"]):
        print(c)
        k_G = normalized_kirchhoff_index(G)

        kirchhoff_indexes = {}
        kirchhoff_indexes_list = []
        for u, v in G.edges():
            k = effective_edge_resistance_centrality(u, v, G, k_G)
            if k == float("inf"):
                continue
            kirchhoff_indexes[(u, v)] = k
            kirchhoff_indexes_list.append(k)

        q = np.quantile(kirchhoff_indexes_list, 0.95)

        m = graph_to_folium(G, c)
        for node1, node2 in G.edges():
            if (node1, node2) not in kirchhoff_indexes or kirchhoff_indexes[(node1, node2)] < q: continue

            if node1 in G.nodes and node2 in G.nodes and 'geometry' in G.nodes[node1] and 'geometry' in G.nodes[node2]:
                geom1 = G.nodes[node1]['geometry']
                geom2 = G.nodes[node2]['geometry']
                if isinstance(geom1, Point) and isinstance(geom2, Point):
                    lat1, lon1 = geom1.y, geom1.x
                    lat2, lon2 = geom2.y, geom2.x
                    folium.PolyLine([[lat1, lon1], [lat2, lon2]], color='orange', weight=2).add_to(m)
                else:
                    print(f"Warning: Skipping edge between {node1} and {node2} due to non-Point geometry.")
            else:
                print(f"Warning: Skipping edge between {node1} and {node2} because one or both nodes are missing geometry information.")

        print("cutoff", q)
        m.save(f"src/visualizations/resistance_{c}_edge.html")  


if __name__ == "__main__":
    main()