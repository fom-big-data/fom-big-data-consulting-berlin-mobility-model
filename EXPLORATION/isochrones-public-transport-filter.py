import csv
import json
from os import path

import ogr
from geojson import FeatureCollection
from tqdm import tqdm


#
# New
#

def filter_geojson(file_path, banned_polygons):
    # Read geojson
    geojson = read_geojson(file_name)

    features = geojson['features']
    filtered_features = []
    banned_count = 0

    for i, feature in tqdm(enumerate(features)):
        coordinates = feature['geometry']['coordinates']

        if not is_in_banned_polygons(coordinates, banned_polygons):
            filtered_features.append(feature)
        else:
            banned_count += 1

    print("Filter " + file_path + ".filtered with " + str(banned_count) + " banned points")

    with open(file_path, "w") as f:
        f.write("%s" % FeatureCollection(filtered_features))


def read_geojson(file_name):
    with open(file_name) as f:
        return json.load(f)


def read_banned_points(file_path):
    with open(file_path, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")

        banned_points = []

        for lon, lat in reader:
            banned_points.append({"lon": lon, "lat": lat})

    return banned_points


def read_banned_polygons():
    banned_polygons = []

    hobrechtsfelde = create_rectangular_polygon(xmin=13.463047742843628, xmax=13.487488031387329,
                                                ymin=52.65753934266786, ymax=52.673161953673485)
    schoenerlinde = create_rectangular_polygon(xmin=13.434755802154541, xmax=13.454807996749878,
                                               ymin=52.63490561092806, ymax=52.64950788953237)
    karow = create_rectangular_polygon(xmin=13.47723441028595, xmax=13.506147695541382,
                                       ymin=52.58581321385924, ymax=52.60220347187549)
    erkner = create_rectangular_polygon(xmin=13.70769517326355, xmax=13.739564252853394,
                                        ymin=52.39768761672284, ymax=52.41336735074955)
    schmoeckwitz = create_rectangular_polygon(xmin=13.687042163848877, xmax=13.698644472122192,
                                              ymin=52.36751176021483, ymax=52.37788291231777)
    thermometer = create_rectangular_polygon(xmin=13.301007913589478, xmax=13.335881067276001,
                                             ymin=52.40174288931766, ymax=52.41186540546308)
    gatow = create_rectangular_polygon(xmin=13.134356903076172, xmax=13.177544904708862,
                                       ymin=52.47563143070943, ymax=52.4954220187933)

    banned_polygons.append(hobrechtsfelde)
    banned_polygons.append(schoenerlinde)
    banned_polygons.append(karow)
    banned_polygons.append(erkner)
    banned_polygons.append(schmoeckwitz)
    banned_polygons.append(thermometer)
    banned_polygons.append(gatow)

    write_polygons_to_geojson("../results/debug-banned-polygons.geojson", banned_polygons)

    return banned_polygons


def create_rectangular_polygon(xmin, xmax, ymin, ymax):
    outline = ogr.Geometry(ogr.wkbLinearRing)
    outline.AddPoint(xmin, ymin)
    outline.AddPoint(xmax, ymin)
    outline.AddPoint(xmax, ymax)
    outline.AddPoint(xmin, ymax)
    outline.AddPoint(xmin, ymin)

    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(outline)

    return polygon


def write_polygons_to_geojson(file_path, polygons):
    if not path.exists(file_path):
        print("Save " + file_path)

        features = []

        for polygon in polygons:
            feature = {}
            feature["geometry"] = polygon.ExportToJson()
            feature["type"] = "Feature"
            features.append(feature)

        collection = FeatureCollection(features)

        with open(file_path, "w") as f:
            f.write("%s" % collection)
    else:
        print("Exists " + file_path)


def is_in_banned_list(coordinates, banned_points):
    lon = coordinates[0]
    lat = coordinates[1]

    for point in banned_points:
        banned_lon = point["lon"]
        banned_lat = point["lat"]

        if lon == banned_lon and lat == banned_lat:
            return True

    return False


def is_in_banned_polygons(coordinates, banned_polygons):
    lon = coordinates[1]
    lat = coordinates[0]

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(float(lat), float(lon))

    for polygon in banned_polygons:
        if point.Within(polygon):
            return True

    return False


#
# Main
#

# Read banned polygons
banned_polygons = read_banned_polygons()

# Iterate over geojson files to filter
for file_name in ['../results/isochrones-all-15.geojson',
                  '../results/isochrones-bike-15.geojson',
                  '../results/isochrones-bus-15.geojson',
                  '../results/isochrones-drive-15.geojson',
                  '../results/isochrones-light_rail-15.geojson',
                  '../results/isochrones-subway-15.geojson',
                  '../results/isochrones-tram-15.geojson',
                  ]:
    filtered_geojson = filter_geojson(file_name, banned_polygons)

print("Complete!")
