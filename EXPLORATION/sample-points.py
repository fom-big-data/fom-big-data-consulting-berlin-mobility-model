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


def get_random_points_in_polygons(polygons_districts,
                                  polygons_cemetery,
                                  polygons_farmland,
                                  polygons_farmyard,
                                  polygons_forest,
                                  polygons_garden,
                                  polygons_park,
                                  polygons_recreation_ground,
                                  polygons_water,
                                  polygons_wood,
                                  num_point):
    points = []
    xmin = None
    ymin = None
    xmax = None
    ymax = None

    for polygon in polygons_districts:

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
    fail_counter = 0
    while counter < num_point:

        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(random.uniform(xmin, xmax),
                       random.uniform(ymin, ymax))

        if is_in_desired_area(point,
                              polygons_districts,
                              polygons_cemetery,
                              polygons_farmland,
                              polygons_farmyard,
                              polygons_forest,
                              polygons_garden,
                              polygons_park,
                              polygons_recreation_ground,
                              polygons_water,
                              polygons_wood):

            points.append(point)
            counter += 1
            print(counter)
        else:
            fail_counter += 1

    print("failed " + str(fail_counter))

    return points


def is_in_desired_area(point,
                       polygons_districts,
                       polygons_cemetery,
                       polygons_farmland,
                       polygons_farmyard,
                       polygons_forest,
                       polygons_garden,
                       polygons_park,
                       polygons_recreation_ground,
                       polygons_water,
                       polygons_wood):
    in_district = False
    for polygon in polygons_districts:
        if point.Within(polygon):
            in_district = True

    if not in_district:
        return False

    for polygon in polygons_cemetery:
        if point.Within(polygon):
            print("in cemetery")
            return False

    for polygon in polygons_farmland:
        if point.Within(polygon):
            print("in farmland")
            return False

    for polygon in polygons_farmyard:
        if point.Within(polygon):
            print("in farmyard")
            return False

    for polygon in polygons_forest:
        if point.Within(polygon):
            print("in forest")
            return False

    for polygon in polygons_garden:
        if point.Within(polygon):
            print("in garden")
            return False

    for polygon in polygons_park:
        if point.Within(polygon):
            print("in park")
            return False

    for polygon in polygons_recreation_ground:
        if point.Within(polygon):
            print("in recreation ground")
            return False

    for polygon in polygons_water:
        if point.Within(polygon):
            print("in water")
            return False

    for polygon in polygons_wood:
        if point.Within(polygon):
            print("in wood")
            return False

    return True


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

# Get polygons
polygons_districts = get_polygons(read_geojson('../data/inhabitants/berlin-inhabitants.geojson'))
polygons_cemetery = get_polygons(read_geojson('../results/cemetery.geojson'))
polygons_farmland = get_polygons(read_geojson('../results/farmland.geojson'))
polygons_farmyard = get_polygons(read_geojson('../results/farmyard.geojson'))
polygons_forest = get_polygons(read_geojson('../results/forest.geojson'))
polygons_garden = get_polygons(read_geojson('../results/garden.geojson'))
polygons_park = get_polygons(read_geojson('../results/park.geojson'))
polygons_recreation_ground = get_polygons(read_geojson('../results/recreation_ground.geojson'))
polygons_water = get_polygons(read_geojson('../results/water.geojson'))
polygons_wood = get_polygons(read_geojson('../results/wood.geojson'))

# Generate points in polygons
points = get_random_points_in_polygons(polygons_districts,
                                       polygons_cemetery,
                                       polygons_farmland,
                                       polygons_farmyard,
                                       polygons_forest,
                                       polygons_garden,
                                       polygons_park,
                                       polygons_recreation_ground,
                                       polygons_water,
                                       polygons_wood,
                                       NUM_POINTS)

# Get coordinates
coords = get_coordinates(points)

# Write coords to file
write_coords_to_json(coords, '../results/sample-points.json')
write_coords_to_csv(coords, '../results/sample-points.csv')
write_coords_to_geojson(coords, '../results/sample-points.geojson')
