import csv
from os import path

import geopy.distance
import networkx as nx
import numpy as np
import osmnx as ox
from geojson import FeatureCollection
from shapely.geometry import MultiPoint
from tqdm import tqdm


def load_graphml_from_file(filepath, place_name, network_type=None, custom_filter=None):
    if not path.exists(filepath):
        graph = load_graphml(place_name, network_type=network_type, custom_filter=custom_filter)
        ox.save_graphml(graph, filepath=filepath)
    else:
        return ox.io.load_graphml(filepath=filepath)


def load_graphml(place_name, network_type=None, custom_filter=None):
    return ox.graph.graph_from_place(place_name, retain_all=True, buffer_dist=2500, network_type=network_type,
                                     custom_filter=custom_filter)


def load_sample_points(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_with_spatial_distance(g, points, travel_time_min):
    points_with_spatial_distance = []
    failed_points = []

    progress_bar = tqdm(iterable=range(len(points)), unit='points', desc="Evaluate points")
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
            "mean_spatial_distance_15min": mean_spatial_distance,
        }

        if mean_spatial_distance > 0:
            mean_spatial_distances.append(mean_spatial_distance)
            points_with_spatial_distance.append(point_with_spatial_distance)
        else:
            failed_points.append(point_with_spatial_distance)

    return points_with_spatial_distance, failed_points


def get_mean_spatial_distance(g, start_point, travel_time_min, real_speed=True):
    try:
        # print("OKAY " + str(start_point))
        nodes, edges = get_possible_routes(g, start_point, travel_time_min, real_speed)

        longitudes, latitudes = get_convex_hull(nodes)
        distances = get_distances(start_point, latitudes, longitudes)
        return np.mean(distances)
    except:
        print("FAIL " + str(start_point))
        return 0


def get_possible_routes(g, start_point, travel_time_min, real_speed=True):
    center_node = ox.get_nearest_node(g, start_point)
    distance_type = 'real_time' if real_speed else 'time'
    subgraph = nx.ego_graph(g, center_node, radius=travel_time_min, distance=distance_type)
    return ox.graph_to_gdfs(subgraph)


def get_convex_hull(nodes):
    return MultiPoint(nodes.reset_index()['geometry']).convex_hull.exterior.coords.xy


def get_distances(start_point, latitudes, longitudes):
    return [geopy.distance.geodesic(point, start_point).meters for point in zip(latitudes, longitudes)]


def write_coords_to_geojson(coords, file_path):
    features = []
    for coord in coords:
        feature = {}
        feature["geometry"] = {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]}
        feature["type"] = "Feature"
        feature["properties"] = {"mean_spatial_distance_15min": coord["mean_spatial_distance_15min"]}
        features.append(feature)

    collection = FeatureCollection(features)

    with open(file_path, 'w') as f:
        f.write('%s' % collection)


#
# Main
#

PLACE_NAME = "Berlin, Germany"
TRAVEL_TIME_MIN = 15

mean_spatial_distances = []

# Load and compose bus and walk graphs
gBus = load_graphml_from_file('tmp/bus.graphml', PLACE_NAME, custom_filter='["bus"]')
gWalk = load_graphml_from_file('tmp/walk.graphml', PLACE_NAME, network_type='walk')
g = nx.algorithms.operators.all.compose_all([gBus, gWalk])

# Load sample points
sample_points = load_sample_points("../results/sample-points.csv")

# Generate points
points_with_spatial_distance, failed_points = get_points_with_spatial_distance(g, sample_points, TRAVEL_TIME_MIN)

# Write coords to file
write_coords_to_geojson(points_with_spatial_distance, '../results/isochrones-bus.geojson')
write_coords_to_geojson(failed_points, '../results/isochrones-bus-failed.geojson')

print("Complete!")
print("min distance " + str(min(mean_spatial_distances)))
print("max distance " + str(max(mean_spatial_distances)))
