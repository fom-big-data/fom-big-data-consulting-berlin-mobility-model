import csv

from geojson import Feature, FeatureCollection, Point

features = []
with open('../data/vbb-track-gtfs/extracted/stops.txt', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', )
    next(reader)

    for stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, location_type, parent_station, wheelchair_boarding, platform_code, zone_id in reader:

        if (stop_name.startswith('S ') or stop_name.startswith('U ') or stop_name.startswith('S+U ')):
            features.append(
                Feature(
                    geometry=Point((float(stop_lon), float(stop_lat))),
                    properties={
                        'stop-name': stop_name
                    }
                )
            )

collection = FeatureCollection(features)
with open('../results/vbb-stations-s-u-bahn.geojson', 'w') as f:
    f.write('%s' % collection)
