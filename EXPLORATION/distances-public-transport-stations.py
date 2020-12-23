import csv
from os import path

import networkx as nx
import numpy as np
import osmnx as ox
from geojson import FeatureCollection
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
        print("Load " + file_path)
        return ox.io.load_graphml(file_path)


def load_graphml(place_name, network_type=None, custom_filter=None):
    return ox.graph.graph_from_place(query=place_name,
                                     simplify=False,
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

        if transport in ["bus", "light_rail", "subway", "tram"]:
            write_nodes_to_geojson(file_path="../results/stations-" + transport + ".geojson", g=g_transport)

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


def load_sample_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        sample_points = []

        for lon, lat in reader:
            sample_points.append({"lon": lon, "lat": lat})

    return sample_points


def get_points_distances(g_transport_bus,
                         g_transport_light_rail,
                         g_transport_subway,
                         g_transport_tram,
                         points):
    points_with_distances = []
    distances_bus = []
    distances_light_rail = []
    distances_subway = []
    distances_tram = []

    for point_index in tqdm(iterable=range(len(points)),
                            total=len(points),
                            desc="Evaluate points",
                            unit="point"):
        point = points[point_index]
        start_point = (float(point["lat"]), float(point["lon"]))

        distance_bus = get_spatial_distance(g=g_transport_bus, start_point=start_point)
        distance_light_rail = get_spatial_distance(g=g_transport_light_rail, start_point=start_point)
        distance_subway = get_spatial_distance(g=g_transport_subway, start_point=start_point)
        distance_tram = get_spatial_distance(g=g_transport_tram, start_point=start_point)

        distances = [distance_bus, distance_light_rail, distance_subway, distance_tram]

        point_with_distances = {
            "lon": point["lon"],
            "lat": point["lat"],
            "distance_bus": distance_bus,
            "distance_light_rail": distance_light_rail,
            "distance_subway": distance_subway,
            "distance_tram": distance_tram,
            "distance_min": np.min(distances),
            "distance_max": np.max(distances),
            "distance_avg": np.average(distances)
        }

        points_with_distances.append(point_with_distances)

        if distance_bus > 0:
            distances_bus.append(distance_bus)
        if distance_light_rail > 0:
            distances_light_rail.append(distance_bus)
        if distance_subway > 0:
            distances_subway.append(distances_subway)
        if distance_tram > 0:
            distances_tram.append(distances_tram)

    return points_with_distances, \
           distances_bus, \
           distances_light_rail, \
           distances_subway, \
           distances_tram


def get_spatial_distance(g, start_point):
    try:
        _, distance_to_station_meters = ox.get_nearest_node(g, start_point, return_dist=True)
        return distance_to_station_meters
    except:
        return -1


def write_coords_to_geojson(file_path, coords):
    features = []
    for coord in coords:
        feature = {}
        feature["geometry"] = {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]}
        feature["type"] = "Feature"
        feature["properties"] = {
            "distance_bus": coord["distance_bus"],
            "distances_light_rail": coord["distances_light_rail"],
            "distances_subway": coord["distances_subway"],
            "distances_tram": coord["distances_tram"],
            "distance_min": coord["distance_min"],
            "distance_max": coord["distance_max"],
            "distance_avg": coord["distance_avg"],
        }
        features.append(feature)

    collection = FeatureCollection(features)

    with open(file_path, "w") as f:
        f.write("%s" % collection)


def write_nodes_to_geojson(file_path, g):
    if not path.exists(file_path):
        print("Save " + file_path)

        features = []

        if len(g.nodes) > 0:
            for node_id in g.nodes:
                node = g.nodes[node_id]
                feature = {}
                feature["geometry"] = {"type": "Point", "coordinates": [node["x"], node["y"]]}
                feature["type"] = "Feature"
                features.append(feature)

        collection = FeatureCollection(features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def write_distances_to_file(file_path,
                            distances_bus,
                            distances_light_rail,
                            distances_subway,
                            distances_tram):
    with open(file_path, "w") as f:
        f.write("       distance bus " + str(min(distances_bus)) + " / max " + str(max(distances_bus)) + "\n")
        f.write("distance light rail " + str(min(distances_light_rail)) + " / max " + str(max(distances_light_rail)) + "\n")
        f.write("    distance subway " + str(min(distances_subway)) + " / max " + str(max(distances_subway)) + "\n")
        f.write("      distance tram " + str(min(distances_tram)) + " / max " + str(max(distances_tram)) + "\n")


def plot_graph(g):
    ox.plot_graph(g)


#
# Main
#

PLACE_NAME = "Berlin, Germany"
OVERRIDE_RESULTS = False

# Load sample points
sample_points = load_sample_points(file_path="../results/sample-points.csv")

# Get graphs for means of transport
g_transport_bus = get_means_of_transport_graph(transport="bus", enhance_with_speed=False)
g_transport_light_rail = get_means_of_transport_graph(transport="light_rail", enhance_with_speed=False)
g_transport_subway = get_means_of_transport_graph(transport="subway", enhance_with_speed=False)
g_transport_tram = get_means_of_transport_graph(transport="tram", enhance_with_speed=False)

result_file_name_base = "../results/distance-public-transport-stations"
result_file_name_base_distances = "../results/distances/distance-public-transport-stations"

if not path.exists(result_file_name_base + ".geojson") or OVERRIDE_RESULTS:
    print(">>> Analyze distances to public transport stations")

    # Generate points
    points_with_distances, \
    distances_bus, \
    distances_light_rail, \
    distances_subway, \
    distances_tram = get_points_distances(g_transport_bus=g_transport_bus,
                                          g_transport_light_rail=g_transport_light_rail,
                                          g_transport_subway=g_transport_subway,
                                          g_transport_tram=g_transport_tram,
                                          points=sample_points)

    # Write results to file
    write_coords_to_geojson(file_path=result_file_name_base + ".geojson",
                            coords=points_with_distances)
    write_distances_to_file(file_path=result_file_name_base_distances + ".txt",
                            distances_bus=distances_bus,
                            distances_light_rail=distances_light_rail,
                            distances_subway=distances_subway,
                            distances_tram=distances_tram)
else:
    print(">>> Exists")

print("Complete!")
