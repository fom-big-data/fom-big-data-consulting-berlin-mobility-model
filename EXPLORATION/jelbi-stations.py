import csv

from geojson import Feature, FeatureCollection, Point

features = []
with open('../data/jelbi/jelbi.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', )
    next(reader)

    for station_name, station_lat, station_lon in reader:

        features.append(
            Feature(
                geometry=Point((float(station_lon), float(station_lat))),
                properties={
                    'station-name': station_name
                }
            )
        )

collection = FeatureCollection(features)
with open('../results/jelbi-stations.geojson', 'w') as f:
    f.write('%s' % collection)
