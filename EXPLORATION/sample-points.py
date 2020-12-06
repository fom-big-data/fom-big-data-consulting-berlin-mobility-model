import csv
import json
import random

from geojson import FeatureCollection
from osgeo import ogr


def read_geojson(file_path):
    file = open(file_path)
    return json.load(file)


def get_polygons(geojson):
    polygons = []

    # Extract polygons from inhabitants file
    features = geojson['features']

    for feature in features:
        geom = feature['geometry']
        geom = json.dumps(geom)
        polygon = ogr.CreateGeometryFromJson(geom)

        polygons.append(polygon)

    return polygons


def get_bounding_box(polygon):
    env = polygon.GetEnvelope()
    return env[0], env[2], env[1], env[3]


def get_random_points_in_polygons(polygons, num_point):
    points = []
    xmin = None
    ymin = None
    xmax = None
    ymax = None

    for polygon in polygons:

        # Get bounding box
        boundingXmin, boundingYmin, boundingXmax, boundingYmax = get_bounding_box(polygon)

        if xmin == None or boundingXmin < xmin:
            xmin = boundingXmin
        if ymin == None or boundingYmin < ymin:
            ymin = boundingYmin
        if xmax == None or boundingXmax > xmax:
            xmax = boundingXmax
        if ymax == None or boundingYmax > ymax:
            ymax = boundingYmax


    counter = 0
    while counter < num_point:

        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(random.uniform(xmin, xmax),
                       random.uniform(ymin, ymax))

        for polygon in polygons:
            if point.Within(polygon):
                points.append(point)

                counter += 1

    return points


def get_coordinates(points):
    data = []
    for p in points:
        coord = {}
        coord["lon"] = p.GetX()
        coord["lat"] = p.GetY()
        data.append(coord)

    return data


def write_coords_to_json(coords, file_path):
    json_data = json.dumps(coords)
    with open(file_path, 'w') as f:
        f.write('%s' % json_data)


def write_coords_to_csv(coords, file_path):
    with open(file_path, 'w') as f:
        writer = csv.writer(f)
        for coord in coords:
            writer.writerow([coord["lon"], coord["lat"]])


def write_coords_to_geojson(coords, file_path):
    features = []
    for coord in coords:
        feature = {}
        feature["geometry"] = {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]}
        feature["type"] = "Feature"
        features.append(feature)

    collection = FeatureCollection(features)

    with open(file_path, 'w') as f:
        f.write('%s' % collection)


#
# Main
#

NUM_POINTS = 10_000

# Read berlin-inhabitants.geojson
geojson = read_geojson('../data/inhabitants/berlin-inhabitants.geojson')

# Get polygons
polygons = get_polygons(geojson)

# Generate points in polygons
points = get_random_points_in_polygons(polygons, NUM_POINTS)

# Get coordinates
coords = get_coordinates(points)

# Write coords to file
write_coords_to_json(coords, '../results/sample-points.json')
write_coords_to_csv(coords, '../results/sample-points.csv')
write_coords_to_geojson(coords, '../results/sample-points.geojson')
