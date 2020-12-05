import csv
from os import path
from tqdm import tqdm
import geopy.distance
import networkx as nx
import numpy as np
import osmnx as ox
from geojson import FeatureCollection
from shapely.geometry import MultiPoint
from shapely.geometry import LineString


def download_graphml(place_name, custom_filter, filepath):
    print("download_graphmal")
    if not path.exists(filepath):
        graph = load_graphml(place_name, custom_filter)
        ox.save_graphml(graph, filepath=filepath)
        print("download finished")
    else:
        print("download unnecessary")


def load_graphml(place_name, custom_filter):
    return ox.graph.graph_from_place(place_name, retain_all=True, buffer_dist=2500, custom_filter=custom_filter)


def load_sample_points(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_with_spatial_distance(g, points, travel_time_min):
    points_with_spatial_distance = []

    progress_bar = tqdm(iterable=range(len(points)), unit='points', desc="Evaluate points")
    for point_index in progress_bar:

        point = points[point_index]
        start_point = (float(point["lat"]), float(point["lon"]))
        mean_spatial_distance = get_mean_spatial_distance(g=g,
                                                          start_point=start_point,
                                                          travel_time_min=travel_time_min,
                                                          real_speed=True)

        mean_spatial_distances.append(mean_spatial_distance)

        nearest_node_id = ox.get_nearest_node(g, start_point)
        nearest_node = g.nodes[nearest_node_id]

        point_with_spatial_distance = {
            "lon": nearest_node["x"],
            "lat": nearest_node["y"],
            "mean_spatial_distance_15min": mean_spatial_distance,
        }

        points_with_spatial_distance.append(point_with_spatial_distance)

    return points_with_spatial_distance


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
    return MultiPoint(nodes.reset_index()['geometry']).convex_hull.coords.xy


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

# Load bus graph
g = load_graphml(PLACE_NAME, '["bus"="yes"]')

# Load sample points
sample_points = load_sample_points("../results/sample-points.csv")

points_with_spatial_distance = get_points_with_spatial_distance(g, sample_points[:5000], TRAVEL_TIME_MIN)

# Write coords to file
write_coords_to_geojson(points_with_spatial_distance, '../results/isochrones-bus.geojson')

print("Complete!")
print("min distance " + str(min(mean_spatial_distances)))
print("max distance " + str(max(mean_spatial_distances)))