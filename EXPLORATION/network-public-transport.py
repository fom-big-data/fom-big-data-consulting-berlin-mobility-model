from os import path

import networkx as nx
import osmnx as ox
from geojson import FeatureCollection


def load_graphml_from_file(file_path, place_name, network_type=None, custom_filter=None):
    if not path.exists(file_path):
        print("Download " + file_path)
        graph = load_graphml(place_name=place_name,
                             network_type=network_type,
                             custom_filter=custom_filter)
        ox.save_graphml(graph, file_path)
        return graph
    else:
        print("Load " + file_path)
        return ox.io.load_graphml(file_path)


def load_graphml(place_name, network_type=None, custom_filter=None):
    return ox.graph.graph_from_place(query=place_name,
                                     simplify=True,
                                     retain_all=False,
                                     buffer_dist=2500,
                                     network_type=network_type,
                                     custom_filter=custom_filter)


def get_means_of_transport_graph(transport, enhance_with_speed=False):
    if transport == "all":
        return nx.algorithms.operators.all.compose_all([get_means_of_transport_graph(transport="bus", enhance_with_speed=True),
                                                        get_means_of_transport_graph(transport="subway", enhance_with_speed=True),
                                                        get_means_of_transport_graph(transport="tram", enhance_with_speed=True),
                                                        get_means_of_transport_graph(transport="light_rail", enhance_with_speed=True)])
    else:
        g_transport = None

        if transport == "walk":
            g_transport = load_graphml_from_file(file_path='tmp/walk.graphml',
                                                 place_name=PLACE_NAME,
                                                 network_type='walk')
        elif transport == "bike":
            g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                                 place_name=PLACE_NAME,
                                                 network_type='bike')
        elif transport == "bus":
            g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                                 place_name=PLACE_NAME,
                                                 custom_filter='["highway"~"secondary|tertiary|residential|bus_stop"]')
        elif transport == "light_rail":
            g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                                 place_name=PLACE_NAME,
                                                 custom_filter='["railway"~"light_rail|station"]["railway"!="light_rail_entrance"]["railway"!="service_station"]["station"!="subway"]')
        elif transport == "subway":
            g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                                 place_name=PLACE_NAME,
                                                 custom_filter='["railway"~"subway|station"]["railway"!="subway_entrance"]["railway"!="service_station"]["station"!="light_rail"]["service"!="yard"]')
        elif transport == "tram":
            g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                                 place_name=PLACE_NAME,
                                                 custom_filter='["railway"~"tram|tram_stop"]["railway"!="tram_crossing"]["train"!="yes"]["station"!="subway"]["station"!="light_rail"]')

        return g_transport


def write_net_to_geojson(file_path, g):
    if not path.exists(file_path):
        print("Save " + file_path)

        edge_features = get_edge_features(g)
        node_features = get_node_features(g)
        collection = FeatureCollection(edge_features + node_features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def write_nodes_to_geojson(file_path, g):
    if not path.exists(file_path):
        print("Save " + file_path)


        node_features = get_node_features(g)
        collection = FeatureCollection(node_features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def write_edges_to_geojson(file_path, g):
    if not path.exists(file_path):
        print("Save " + file_path)

        edge_features = get_edge_features(g)
        collection = FeatureCollection(edge_features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def get_edge_features(g):
    features = []

    if len(g.edges) > 0:
        for node_ids in g.edges:
            node_start = g.nodes[node_ids[0]]
            node_end = g.nodes[node_ids[1]]
            feature = {}
            feature["geometry"] = {"type": "LineString", "coordinates": [[node_start["x"], node_start["y"]],
                                                                         [node_end["x"], node_end["y"]]]}
            feature["type"] = "Feature"
            features.append(feature)

    return features


def get_node_features(g):
    features = []

    if len(g.nodes) > 0:
        for node_id in g.nodes:
            node = g.nodes[node_id]
            feature = {}
            feature["geometry"] = {"type": "Point", "coordinates": [node["x"], node["y"]]}
            feature["type"] = "Feature"
            features.append(feature)

    return features

#
# Main
#

PLACE_NAME = "Berlin, Germany"
MEANS_OF_TRANSPORT = ["bus", "light_rail", "subway", "tram"]
OVERRIDE_RESULTS = False

# Iterate over means of transport
for transport in MEANS_OF_TRANSPORT:

    # Get graph for means of transport
    g_transport = get_means_of_transport_graph(transport=transport, enhance_with_speed=True)
    # Write network to geojson
    write_net_to_geojson(file_path="../results/net-" + transport + ".geojson", g=g_transport)
    write_edges_to_geojson(file_path="../results/lines-" + transport + ".geojson", g=g_transport)
    write_nodes_to_geojson(file_path="../results/stations-" + transport + ".geojson", g=g_transport)

print("Complete!")
