import json
from shapely.geometry import shape
from networkx.readwrite import json_graph

def graph_from_geojson(path, directed=False, multigraph=True):
    """
    Read a JSON file at 'path' produced by graph_to_geojson and
    reconstruct the original NetworkX graph with Shapely geometries.
    """
    # 1. Load the raw node-link dict
    with open(path) as f:
        data = json.load(f)

    # 2. Convert each node's GeoJSON dict back into a Shapely geometry
    for node_obj in data.get("nodes", []):
        geom_dict = node_obj.get("geometry")
        if isinstance(geom_dict, dict) and "type" in geom_dict:
            node_obj["geometry"] = shape(geom_dict)  # inverse of to_geojson :contentReference[oaicite:1]{index=1}

    # 3. (Optional) If you stored edge geometries similarly, undo those too
    for edge_obj in data.get("links", data.get("edges", [])):
        geom_dict = edge_obj.get("geometry")
        if isinstance(geom_dict, dict) and "type" in geom_dict:
            edge_obj["geometry"] = shape(geom_dict)

    # 4. Rebuild the NetworkX graph (with all attrs, including restored geometries)
    G = json_graph.node_link_graph(
        data,
        directed=directed,
        multigraph=multigraph
    )  # rebuilds Graph from node-link format :contentReference[oaicite:2]{index=2}

    return G