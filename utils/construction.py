import json
from shapely import to_geojson
from shapely.geometry import shape
from networkx.readwrite import json_graph

def graph_to_geojson(G, path):
    """
    Serialize NetworkX graph G (with Shapely geometries in node attrs)
    to a JSON file at 'path', converting geometries via to_geojson.
    """
    # 1. Extract node-link data
    data = json_graph.node_link_data(G)
    # 2. Replace each geometry attribute with a GeoJSON dict
    for node in data["nodes"]:
        geom = node.get("geometry")
        if geom is not None:
            # to_geojson returns a JSON string; parse it
            geojson_str = to_geojson(geom, indent=None)
            node["geometry"] = json.loads(geojson_str)
    # 3. Dump to file
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


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
        multigraph=multigraph,
        edges="links"
    )  # rebuilds Graph from node-link format :contentReference[oaicite:2]{index=2}

    return G
