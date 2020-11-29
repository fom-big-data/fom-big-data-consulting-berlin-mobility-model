import json
import os

from geojson import Feature, FeatureCollection, Point
#
# features = []
# f = open('../data/nextbike-stations/nextbike-stations.json')
# stations = json.load(f)
#
# #print(stations)
#
# for station_id,name,short_name,region_id,capacity,lat,lon in stations:
#
#         features.append(
#             Feature(
#                 geometry= Point(lat, lon),
#                 properties={
#                     'name': name,
#                     'station_id': station_id,
#                     'short_name': short_name,
#                     'region_id': region_id,
#                     'capacity': capacity
#                     }
#                 )
#             )
#
# collection = FeatureCollection(features)
# with open('../results/nextbike-stations.geojson', 'w') as f:
#     f.write('%s' % collection)

f = open('../data/nextbike-stations/nextbike-stations.json')
stations = json.load(f)['data']['stations']

places = []
for station in stations:
    placegeojson = {}
    placegeojson["geometry"] = {"type": "Point", "coordinates": [station["lat"], station["lon"]]}
    placegeojson["type"] = "Feature"
    placegeojson["properties"] = {"name": station["name"],
                                  "station_id": station["station_id"],
                                  "short_name": station["short_name"],
                                  "region_id": station["region_id"],
                                  # "capacity": station["capacity"]
                                  }

    places.append(placegeojson)

collection = FeatureCollection(places)
with open('../results/nextbike-stations.geojson', 'w') as f:
     f.write('%s' % collection)