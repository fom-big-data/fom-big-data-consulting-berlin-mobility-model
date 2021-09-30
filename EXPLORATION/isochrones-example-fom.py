import csv
from os import path

import networkx as nx
import osmnx as ox
from geojson import FeatureCollection
from tqdm import tqdm
from shapely.geometry import MultiPoint



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

        if enhance_with_speed:
            return enhance_graph_with_speed(g=g_transport, transport=transport)
        else:
            return g_transport


def enhance_graph_with_speed(g, time_attribute='time', transport=None):
    for _, _, _, data in g.edges(data=True, keys=True):

        speed = None

        if (transport == 'walk'):
            speed = 6.0
        elif (transport == 'bus'):
            speed = 19.5
        elif (transport == 'bike'):
            speed = 16.0
        elif (transport == 'subway'):
            speed = 31.0
        elif (transport == 'tram'):
            speed = 19.0
        elif (transport == 'rail'):
            speed = 38.0

        if speed is not None:
            data[time_attribute] = data['length'] / (float(speed) * 1000 / 60)

    return g


def compose_graphs(file_path, g_a, g_b, connect_a_to_b=False):
    """
    Composes two graphs into one

    Parameters
    ----------
    :param g_a : MultiDiGraph First graph.
    :param g_b : MultiDiGraph Second graph.
    :param connect_a_to_b : bool If true, each node of first graph will be connected to the closest node of the second graph via an edge
    :return composed graph
    """
    g = nx.algorithms.operators.all.compose_all([g_a, g_b])

    if connect_a_to_b:
        a_nodes, a_edges = ox.graph_to_gdfs(g_a)
        b_nodes, b_edges = ox.graph_to_gdfs(g_b)

        # Iterate over all nodes of first graph
        for key, a_node_id in tqdm(iterable=a_nodes["osmid"].items(),
                                   desc="Compose graphs",
                                   total=len(a_nodes),
                                   unit="point"):
            # Get coordinates of node
            a_nodes_point = g_a.nodes[a_node_id]

            # Get node in second graph that is closest to node in first graph
            b_node_id, distance = ox.get_nearest_node(g_b, (a_nodes_point["y"], a_nodes_point["x"]), return_dist=True)

            # Add edges in both directions
            g.add_edge(a_node_id, b_node_id,
                       osmid=0,
                       name="Way from station",
                       highway="tertiary",
                       maxspeed="50",
                       oneway=False,
                       length=0,
                       time=0)
            g.add_edge(b_node_id, a_node_id,
                       osmid=0,
                       name="Way to station",
                       highway="tertiary",
                       maxspeed="50",
                       oneway=False,
                       length=0,
                       time=0)

    ox.save_graphml(g, file_path)
    return g


def load_sample_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_possible_routes(g, start_point, travel_time_minutes, transport, distance_attribute, calculate_walking_distance=False):
    center_node, distance_to_station_meters = ox.get_nearest_node(g, start_point, return_dist=True)

    if calculate_walking_distance:
        walking_speed_meters_per_minute = 100
        walking_time_minutes = distance_to_station_meters / walking_speed_meters_per_minute

        walking_time_minutes_max = walking_time_minutes if walking_time_minutes < travel_time_minutes else travel_time_minutes
        walking_distance_meters = walking_time_minutes_max * walking_speed_meters_per_minute

        radius = travel_time_minutes - walking_time_minutes
    else:
        walking_distance_meters = 0
        radius = travel_time_minutes

    if radius > 0:
        subgraph = nx.ego_graph(g, center_node, radius=radius, distance=distance_attribute)
        nodes, edges = ox.graph_to_gdfs(subgraph)

        write_nodes_to_geojson("../results/isochrones-" + transport + "-" + str(travel_time_minutes) + "-" + str(start_point[0]) + "-" +
                               str(start_point[1]) + ".geojson", subgraph)
        write_convex_hull_to_geojson("../results/isochrones-hull-" + transport + "-" + str(travel_time_minutes) + "-" + str(start_point[0]) + "-" +
                               str(start_point[1]) + ".geojson", nodes)


def get_convex_hull(nodes):
    return MultiPoint(nodes.reset_index()["geometry"]).convex_hull.exterior.coords.xy


def write_nodes_to_geojson(file_path, g):
    if not path.exists(file_path):
        print("Save " + file_path)


        node_features = get_node_features(g)
        collection = FeatureCollection(node_features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def write_convex_hull_to_geojson(file_path, nodes):
    if not path.exists(file_path):
        longitudes, latitudes = get_convex_hull(nodes)
        features = []

        points = []
        for point in zip(latitudes, longitudes):
            points.append(point)
        # Close line string
        points.append(points[0])

        for i in range(0, len(points)-1):
            start = points[i]
            end = points[i+1]
            feature = {}
            feature["geometry"] = {"type": "LineString", "coordinates": [[start[1], start[0]],
                                                                         [end[1], end[0]]]}
            feature["type"] = "Feature"
            features.append(feature)

        collection = FeatureCollection(features)

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
TRAVEL_TIMES_MINUTES = range(1, 30)
MEANS_OF_TRANSPORT = ["walk", "subway"]
OVERRIDE_RESULTS = False

# Load walk graph
g_walk = get_means_of_transport_graph(transport="walk", enhance_with_speed=True)

# Load sample points
sample_points = load_sample_points(file_path="../results/sample-points-example-fom.csv")

# Iterate over means of transport
for transport in MEANS_OF_TRANSPORT:

    if transport == "walk":
        # Use just walk graph
        g = g_walk
    else:
        # Get graph for means of transport
        g_transport = get_means_of_transport_graph(transport=transport, enhance_with_speed=True)

        # Compose transport graph and walk graph
        g = compose_graphs("tmp/" + transport + "+walk.graphml", g_transport, g_walk, connect_a_to_b=True)

    # Iterate over travel times
    for travel_time_minutes in tqdm(iterable=TRAVEL_TIMES_MINUTES,
                                   desc="Calculate isochrones",
                                   total=len(TRAVEL_TIMES_MINUTES),
                                   unit="isochrone"):

        # Iterate over sample points
        for point_index in range(len(sample_points)):

            point = sample_points[point_index]
            start_point = (float(point["lat"]), float(point["lon"]))

            print(">>> Analyze " + transport + " in " + str(travel_time_minutes) + " minutes")

            get_possible_routes(g, start_point, travel_time_minutes, transport, "time")

print("Complete!")
