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
    return ox.graph.graph_from_place(place_name=place_name,
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
        return load_graphml_from_file(file_path="tmp/" + transport + ".graphml",
                                      place_name=PLACE_NAME,
                                      custom_filter='["railway"~"' + transport + '"]')


def enhance_with_speed(g, time_attribute='time', transport=None):
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


def load_sample_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_with_spatial_distance(g, points, travel_time_min, transport):
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
                                                    travel_time_min=travel_time_min,
                                                    transport=transport)

        nearest_node_id = ox.get_nearest_node(g, start_point)
        nearest_node = g.nodes[nearest_node_id]

        point_with_spatial_distance = {
            "lon": nearest_node["x"],
            "lat": nearest_node["y"],
            "mean_spatial_distance_" + str(travel_time_min) + "min": mean_spatial_distance,
            "median_spatial_distance_" + str(travel_time_min) + "min": median_spatial_distance,
            "min_spatial_distance_" + str(travel_time_min) + "min": min_spatial_distance,
            "max_spatial_distance_" + str(travel_time_min) + "min": max_spatial_distance
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


def get_spatial_distance(g, start_point, travel_time_min, distance_attribute='time', transport=''):
    try:
        # print("OKAY " + str(start_point))
        nodes, edges = get_possible_routes(g, start_point, travel_time_min, distance_attribute)

        # Debug subgraph
        # write_subgraph_to_geojson(nodes, edges, start_point, transport)

        longitudes, latitudes = get_convex_hull(nodes)
        distances = get_distances(start_point, latitudes, longitudes)
        return np.mean(distances), np.median(distances), np.min(distances), np.max(distances)
    except:
        # print("FAIL " + str(start_point))
        return 0, 0, 0, 0


def get_possible_routes(g, start_point, travel_time_min, distance_attribute):
    center_node, distance_to_station = ox.get_nearest_node(g, start_point, return_dist=True)

    walking_speed = 6.0
    walking_time = ((distance_to_station / 1000) / walking_speed) * 60
    radius = travel_time_min - walking_time

    if radius > 0:
        subgraph = nx.ego_graph(g, center_node, radius=radius, distance=distance_attribute)
        return ox.graph_to_gdfs(subgraph)
    else:
        return [], []


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


def write_subgraph_to_geojson(nodes, edges, start_point, transport):
    features = []

    feature = {}
    feature["geometry"] = {"type": "Point", "coordinates": [start_point[0], start_point[1]]}
    feature["type"] = "Feature"
    features.append(feature)

    # if len(nodes) > 0:
    #     for node in MultiPoint(nodes.reset_index()["geometry"]):
    #         feature = {}
    #         feature["geometry"] = {"type": "Point", "coordinates": [node.x, node.y]}
    #         feature["type"] = "Feature"
    #         features.append(feature)

    if len(edges) > 0:
        for edge in edges["geometry"]:
            feature = {}
            feature["geometry"] = {"type": "LineString",
                                   "coordinates": [[edge.bounds[0], edge.bounds[1]], [edge.bounds[2], edge.bounds[3]]]}
            feature["type"] = "Feature"
            features.append(feature)

    collection = FeatureCollection(features)

    file_path = "../results/isochrones-" + transport + "-" + str(travel_time_min) + "-" + str(start_point[0]) + "-" + str(
        start_point[1]) + ".geojson"

    with open(file_path, "w") as f:
        f.write("%s" % collection)


def write_mean_spatial_distances_to_file(mean_spatial_distances,
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
TRAVEL_TIMES = [20, 40, 60]
MEANS_OF_TRANSPORT = ["tram", "subway", "rail", "bus", "bike", "all"]
OVERRIDE_RESULTS = False

# Load walk graph
g_walk = load_graphml_from_file(file_path='tmp/walk.graphml',
                                place_name=PLACE_NAME,
                                network_type='walk')

# Enhance graph with speed
g_walk = enhance_with_speed(g=g_walk, transport='walk')

# Load sample points
sample_points = load_sample_points(file_path="../results/sample-points.csv")

# Iterate over means of transport
for transport in MEANS_OF_TRANSPORT:

    # Get graph for means of transport
    g_transport = get_means_of_transport_graph(transport=transport)

    # Enhance graph with speed
    g_transport = enhance_with_speed(g=g_transport, transport=transport)

    # Iterate over travel times
    for travel_time_min in TRAVEL_TIMES:

        result_file_name_base = "../results/isochrones-" + transport + "-" + str(travel_time_min)

        if not path.exists(result_file_name_base + ".geojson") or OVERRIDE_RESULTS:
            print(">>> Analyze " + transport + " in " + str(travel_time_min) + " minutes")

            # Generate points
            points_with_spatial_distance, \
            failed_points, \
            mean_spatial_distances, \
            median_spatial_distances, \
            min_spatial_distances, \
            max_spatial_distances = get_points_with_spatial_distance(g=g_transport,
                                                                     points=sample_points,
                                                                     travel_time_min=travel_time_min,
                                                                     transport=transport)

            # Write results to file
            write_coords_to_geojson(coords=points_with_spatial_distance,
                                    travel_time_min=travel_time_min,
                                    file_path=result_file_name_base + ".geojson")
            write_coords_to_geojson(coords=failed_points,
                                    travel_time_min=travel_time_min,
                                    file_path=result_file_name_base + "-failed.geojson")
            write_mean_spatial_distances_to_file(mean_spatial_distances=mean_spatial_distances,
                                                 median_spatial_distances=median_spatial_distances,
                                                 min_spatial_distances=min_spatial_distances,
                                                 max_spatial_distances=max_spatial_distances,
                                                 file_path=result_file_name_base + "-distances.txt")
        else:
            print(">>> Exists " + transport + " in " + str(travel_time_min) + " minutes")

print("Complete!")
