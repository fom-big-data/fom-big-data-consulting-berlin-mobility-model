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


def get_means_of_transport_graph(name):
    if name == "all":
        return nx.algorithms.operators.all.compose_all([get_means_of_transport_graph("bike"),
                                                        get_means_of_transport_graph("bus"),
                                                        get_means_of_transport_graph("subway"),
                                                        get_means_of_transport_graph("tram"),
                                                        get_means_of_transport_graph("rail"),
                                                        ])
    if name == "bike":
        return load_graphml_from_file(file_path="tmp/" + name + ".graphml",
                                      place_name=PLACE_NAME,
                                      network_type='bike')
    if name == "bus":
        return load_graphml_from_file(file_path="tmp/" + name + ".graphml",
                                      place_name=PLACE_NAME,
                                      custom_filter='["bus"="yes"]')
    elif name == "subway" or name == "tram" or name == "rail":
        return load_graphml_from_file(file_path="tmp/" + name + ".graphml",
                                      place_name=PLACE_NAME,
                                      custom_filter='["railway"~"' + name + '"]')


def load_sample_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_with_spatial_distance(g, points, travel_time_min):
    points_with_spatial_distance = []
    failed_points = []
    mean_spatial_distances = []

    progress_bar = tqdm(iterable=range(len(points)), unit="points", desc="Evaluate points")
    for point_index in progress_bar:
        point = points[point_index]
        start_point = (float(point["lat"]), float(point["lon"]))
        mean_spatial_distance = get_mean_spatial_distance(g=g,
                                                          start_point=start_point,
                                                          travel_time_min=travel_time_min,
                                                          real_speed=True)

        nearest_node_id = ox.get_nearest_node(g, start_point)
        nearest_node = g.nodes[nearest_node_id]

        point_with_spatial_distance = {
            "lon": nearest_node["x"],
            "lat": nearest_node["y"],
            "mean_spatial_distance_" + str(travel_time_min) + "min": mean_spatial_distance,
        }

        if mean_spatial_distance > 0:
            mean_spatial_distances.append(mean_spatial_distance)
            points_with_spatial_distance.append(point_with_spatial_distance)
        else:
            failed_points.append(point_with_spatial_distance)

    return points_with_spatial_distance, failed_points, mean_spatial_distances


def get_mean_spatial_distance(g, start_point, travel_time_min, real_speed=True):
    try:
        # print("OKAY " + str(start_point))
        nodes, edges = get_possible_routes(g, start_point, travel_time_min, real_speed)

        longitudes, latitudes = get_convex_hull(nodes)
        distances = get_distances(start_point, latitudes, longitudes)
        return np.mean(distances)
    except:
        # print("FAIL " + str(start_point))
        return 0


def get_possible_routes(g, start_point, travel_time_min, real_speed=True):
    center_node = ox.get_nearest_node(g, start_point)
    distance_type = "real_time" if real_speed else "time"
    subgraph = nx.ego_graph(g, center_node, radius=travel_time_min, distance=distance_type)
    return ox.graph_to_gdfs(subgraph)


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
            "mean_spatial_distance_" + str(travel_time_min) + "min": coord["mean_spatial_distance_" + str(travel_time_min) + "min"]}
        features.append(feature)

    collection = FeatureCollection(features)

    with open(file_path, "w") as f:
        f.write("%s" % collection)


def write_mean_spatial_distances_to_file(mean_spatial_distances, file_path):
    with open(file_path, "w") as f:
        f.write("min distance " + str(min(mean_spatial_distances)) + " / max distance " + str(max(mean_spatial_distances)))


#
# Main
#

PLACE_NAME = "Berlin, Germany"
TRAVEL_TIMES = [5, 10, 15]
MEANS_OF_TRANSPORT = ["all", "bike", "bus", "subway", "tram", "rail"]

# Load complete graph
# g_all = load_graphml_from_file(file_path='tmp/all.graphml', place_name=PLACE_NAME, network_type='all')

# Load walk graph
g_walk = load_graphml_from_file(file_path='tmp/walk.graphml',
                                place_name=PLACE_NAME,
                                network_type='walk')

# Load sample points
sample_points = load_sample_points(file_path="../results/sample-points.csv")

# Iterate over means of transport
for name in MEANS_OF_TRANSPORT:

    # Get graph for means of transport
    g_transport = get_means_of_transport_graph(name=name)

    # Compose means of transport with walking
    g = nx.algorithms.operators.all.compose_all([g_transport, g_walk])

    # Iterate over travel times
    for travel_time_min in TRAVEL_TIMES:

        result_file_name_base = "../results/isochrones-" + name + "-" + str(travel_time_min)

        if not path.exists(result_file_name_base + ".geojson"):
            print(">>> Analyze " + name + " in " + str(travel_time_min) + " minutes")

            # Generate points
            points_with_spatial_distance, \
            failed_points, \
            mean_spatial_distances = get_points_with_spatial_distance(g=g,
                                                                      points=sample_points,
                                                                      travel_time_min=travel_time_min)

            # Write results to file
            write_coords_to_geojson(coords=points_with_spatial_distance,
                                    travel_time_min=travel_time_min,
                                    file_path=result_file_name_base + ".geojson")
            write_coords_to_geojson(coords=failed_points,
                                    travel_time_min=travel_time_min,
                                    file_path=result_file_name_base + "-failed.geojson")
            write_mean_spatial_distances_to_file(mean_spatial_distances=mean_spatial_distances,
                                                 file_path=result_file_name_base + "-distances.txt")
        else:
            print(">>> Exists " + name + " in " + str(travel_time_min) + " minutes")

print("Complete!")
