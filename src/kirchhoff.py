import networkx as nx
import matplotlib.pyplot as plt
from src.util import graph_from_geojson

G: nx.Graph = graph_from_geojson("graphs_with_distance/svk-railroad-network.json")
