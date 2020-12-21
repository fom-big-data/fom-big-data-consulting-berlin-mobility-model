import csv
from os import path

import geopy.distance
import networkx as nx
import numpy as np
import osmnx as ox
from geojson import FeatureCollection
from shapely.geometry import MultiPoint
from tqdm import tqdm


def load_graphml_from_file(file_path, place_name, network_type=None, custom_filter=None):
    if not path.exists(file_path):
        print("Download " + file_path)
        graph = load_graphml(place_name=place_name,
                             network_type=network_type,
                             custom_filter=custom_filter)
        ox.save_graphml(graph, file_path)
        return graph
    else:
        return ox.io.load_graphml(file_path)


def load_graphml(place_name, network_type=None, custom_filter=None):
    return ox.graph.graph_from_place(query=place_name,
                                     retain_all=False,
                                     buffer_dist=2500,
                                     network_type=network_type,
                                     custom_filter=custom_filter)


def get_means_of_transport_graph(transport):
    if transport == "all":
        return nx.algorithms.operators.all.compose_all([get_means_of_transport_graph("bus"),
                                                        get_means_of_transport_graph("subway"),
                                                        get_means_of_transport_graph("tram"),
                                                        get_means_of_transport_graph("rail")])
    if transport == "bike":
        return load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                      place_name=PLACE_NAME,
                                      network_type='bike')
    if transport == "bus":
        return load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                      place_name=PLACE_NAME,
                                      custom_filter='["bus"="yes"]')
    elif transport == "subway" or transport == "tram" or transport == "rail":
        g_transport = load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                             place_name=PLACE_NAME,
                                             custom_filter='["railway"~"' + transport + '"]')

        write_nodes_to_geojson(g_transport, "stations-" + transport + ".geojson")
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
    g = nx.algorithms.operators.all.compose_all([g_a, g_b])

    if connect_a_to_b:
        a_nodes, a_edges = ox.graph_to_gdfs(g_a)
        b_nodes, b_edges = ox.graph_to_gdfs(g_b)

        for a_node_id in a_nodes["osmid"]:
            a_nodes_point = g_a.nodes[a_node_id]
            b_node_id, distance = ox.get_nearest_node(g_b, (a_nodes_point["y"], a_nodes_point["x"]), return_dist=True)
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

    return g


def load_sample_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_with_spatial_distance(g, points, travel_time_minuntes, transport):
    points_with_spatial_distance = []
    failed_points = []
    mean_spatial_distances = []
    median_spatial_distances = []
    min_spatial_distances = []
    max_spatial_distances = []

    progress_bar = tqdm(iterable=range(len(points)), unit="points", desc="Evaluate points")
    for point_index in progress_bar:
        point = points[point_index]
        start_point = (float(point["lat"]), float(point["lon"]))

        mean_spatial_distance, \
        median_spatial_distance, \
        min_spatial_distance, \
        max_spatial_distance = get_spatial_distance(g=g,
                                                    start_point=start_point,
                                                    travel_time_minutes=travel_time_minuntes,
                                                    transport=transport)

        point_with_spatial_distance = {
            "lon": point["lon"],
            "lat": point["lat"],
            "mean_spatial_distance_" + str(travel_time_minuntes) + "min": mean_spatial_distance,
            "median_spatial_distance_" + str(travel_time_minuntes) + "min": median_spatial_distance,
            "min_spatial_distance_" + str(travel_time_minuntes) + "min": min_spatial_distance,
            "max_spatial_distance_" + str(travel_time_minuntes) + "min": max_spatial_distance
        }

        if mean_spatial_distance > 0:
            mean_spatial_distances.append(mean_spatial_distance)
            median_spatial_distances.append(median_spatial_distance)
            min_spatial_distances.append(min_spatial_distance)
            max_spatial_distances.append(max_spatial_distance)
            points_with_spatial_distance.append(point_with_spatial_distance)
        else:
            failed_points.append(point_with_spatial_distance)

    return points_with_spatial_distance, \
           failed_points, \
           mean_spatial_distances, \
           median_spatial_distances, \
           min_spatial_distances, \
           max_spatial_distances


def get_spatial_distance(g, start_point, travel_time_minutes, distance_attribute='time', transport=''):
    walking_distance_meters = 0

    try:
        nodes, edges, walking_distance_meters = get_possible_routes(g,
                                                                    start_point,
                                                                    travel_time_minutes,
                                                                    distance_attribute)

        longitudes, latitudes = get_convex_hull(nodes)
        transport_distances_meters = get_distances(start_point, latitudes, longitudes)

        return np.mean(transport_distances_meters) + walking_distance_meters, \
               np.median(transport_distances_meters) + walking_distance_meters, \
               np.min(transport_distances_meters) + walking_distance_meters, \
               np.max(transport_distances_meters) + walking_distance_meters
    except:
        return walking_distance_meters, walking_distance_meters, walking_distance_meters, walking_distance_meters


def get_possible_routes(g, start_point, travel_time_minutes, distance_attribute, calculate_walking_distance=False):
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

        # write_nodes_to_geojson(subgraph, "debug-" + str(start_point[0]) + "-" + str(start_point[1]) + ".geojson")

        nodes, edges = ox.graph_to_gdfs(subgraph)
        return nodes, edges, walking_distance_meters
    else:
        return [], [], walking_distance_meters


def get_convex_hull(nodes):
    return MultiPoint(nodes.reset_index()["geometry"]).convex_hull.exterior.coords.xy


def get_distances(start_point, latitudes, longitudes):
    return [geopy.distance.geodesic(point, start_point).meters for point in zip(latitudes, longitudes)]


def write_coords_to_geojson(coords, travel_time_min, file_path):
    features = []
    for coord in coords:
        feature = {}
        feature["geometry"] = {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]}
        feature["type"] = "Feature"
        feature["properties"] = {
            "mean_spatial_distance_" + str(travel_time_min) + "min": coord["mean_spatial_distance_" + str(travel_time_min) + "min"],
            "median_spatial_distance_" + str(travel_time_min) + "min": coord["median_spatial_distance_" + str(travel_time_min) + "min"],
            "min_spatial_distance_" + str(travel_time_min) + "min": coord["min_spatial_distance_" + str(travel_time_min) + "min"],
            "max_spatial_distance_" + str(travel_time_min) + "min": coord["max_spatial_distance_" + str(travel_time_min) + "min"],
        }
        features.append(feature)

    collection = FeatureCollection(features)

    with open(file_path, "w") as f:
        f.write("%s" % collection)


def write_nodes_to_geojson(g, file_name):
    features = []

    if len(g.nodes) > 0:
        for node_id in g.nodes:
            node = g.nodes[node_id]
            feature = {}
            feature["geometry"] = {"type": "Point", "coordinates": [node["x"], node["y"]]}
            feature["type"] = "Feature"
            features.append(feature)

    collection = FeatureCollection(features)

    file_path = "../results/" + file_name

    with open(file_path, "w") as f:
        f.write("%s" % collection)


def write_spatial_distances_to_file(mean_spatial_distances,
                                    median_spatial_distances,
                                    min_spatial_distances,
                                    max_spatial_distances,
                                    file_path):
    with open(file_path, "w") as f:
        f.write("  mean distance min " + str(min(mean_spatial_distances)) + " / max " + str(max(mean_spatial_distances)) + "\n")
        f.write("median distance min " + str(min(median_spatial_distances)) + " / max " + str(max(median_spatial_distances)) + "\n")
        f.write("   min distance min " + str(min(min_spatial_distances)) + " / max " + str(max(min_spatial_distances)) + "\n")
        f.write("   max distance min " + str(min(max_spatial_distances)) + " / max " + str(max(max_spatial_distances)) + "\n")


def plot_graph(g):
    ox.plot_graph(g)


#
# Main
#

PLACE_NAME = "Berlin, Germany"
TRAVEL_TIMES_MINUTES = [20]
MEANS_OF_TRANSPORT = ["subway"]
OVERRIDE_RESULTS = False

# Load walk graph
g_walk = load_graphml_from_file(file_path='tmp/walk.graphml',
                                place_name=PLACE_NAME,
                                network_type='walk')

g_walk_nodes, g_walk_edges = ox.graph_to_gdfs(g_walk)

# Enhance graph with speed
g_walk = enhance_graph_with_speed(g=g_walk, transport='walk')

# Load sample points
sample_points = load_sample_points(file_path="../results/sample-points-debug.csv")

# Iterate over means of transport
for transport in MEANS_OF_TRANSPORT:

    # Get graph for means of transport
    g_transport = get_means_of_transport_graph(transport=transport)

    # Enhance graph with speed
    g_transport = enhance_graph_with_speed(g=g_transport, transport=transport)

    # Compose transport graph and walk graph
    g = compose_graphs("tmp/" + transport + "+walk.graphml", g_transport, g_walk, connect_a_to_b=True)

    g_walk_nodes, g_walk_edges = ox.graph_to_gdfs(g_walk)
    g_transport_nodes, g_transport_edges = ox.graph_to_gdfs(g_transport)
    g_nodes, g_edges = ox.graph_to_gdfs(g)

    print("g_walk_edges " + str(len(g_walk_edges)))
    print("g_transport_edges " + str(len(g_transport_edges)))
    print("g_edges " + str(len(g_edges)))

    # Iterate over travel times
    for travel_time_minutes in TRAVEL_TIMES_MINUTES:

        result_file_name_base = "../results/isochrones-debug-6-" + transport + "-" + str(travel_time_minutes)

        if not path.exists(result_file_name_base + ".geojson") or OVERRIDE_RESULTS:
            print(">>> Analyze " + transport + " in " + str(travel_time_minutes) + " minutes")

            # Generate points
            points_with_spatial_distance, \
            failed_points, \
            mean_spatial_distances, \
            median_spatial_distances, \
            min_spatial_distances, \
            max_spatial_distances = get_points_with_spatial_distance(g=g,
                                                                     points=sample_points,
                                                                     travel_time_minuntes=travel_time_minutes,
                                                                     transport=transport)

            # Write results to file
            write_coords_to_geojson(coords=points_with_spatial_distance,
                                    travel_time_min=travel_time_minutes,
                                    file_path=result_file_name_base + ".geojson")
            write_coords_to_geojson(coords=failed_points,
                                    travel_time_min=travel_time_minutes,
                                    file_path=result_file_name_base + "-failed.geojson")
            write_spatial_distances_to_file(mean_spatial_distances=mean_spatial_distances,
                                            median_spatial_distances=median_spatial_distances,
                                            min_spatial_distances=min_spatial_distances,
                                            max_spatial_distances=max_spatial_distances,
                                            file_path=result_file_name_base + "-distances.txt")
        else:
            print(">>> Exists " + transport + " in " + str(travel_time_minutes) + " minutes")

print("Complete!")
