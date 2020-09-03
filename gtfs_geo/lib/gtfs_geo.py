import json
import os
import tempfile
import shutil

import gtfstk


def route_type_to_mode(route_type):
	GTFS_ROUTE_TYPES = {
		0: 'Tram',
		1: 'Subway',
		2: 'Rail',
		3: 'Bus',
		4: 'Ferry',
		5: 'Cable Car',
		6: 'Gondola',
		7: 'Funicular'
    }
	return GTFS_ROUTE_TYPES.get(route_type, "Unknown mode")

def location_type_to_stop_type(location_type):
	LOCATION_TYPES = {
		0: "stops",
		1: "stations",
		2: "entrances",
		3: "generic nodes"
	}
	return LOCATION_TYPES.get(location_type, "Unknown stop types")

def export_gtfs_as_geo(input_gtfs_file, output_file_name):
	working_directory = tempfile.TemporaryDirectory()
	feed = gtfstk.read_gtfs(input_gtfs_file, dist_units='km')

	feed_w_shapes = gtfstk.miscellany.create_shapes(feed)

	# keep only a relevant subset 
	feed_w_shapes_selected = feed_w_shapes.trips[['route_id', 'shape_id', 'trip_id']]
	feed_w_shapes_dedup = feed_w_shapes_selected.drop_duplicates(subset=['route_id', 'shape_id'])

	trip_stats = feed_w_shapes.compute_trip_stats()

	trips_full = feed_w_shapes_dedup.merge(trip_stats, left_on='trip_id', right_on='trip_id', suffixes=('', '_'))
	trips_full_selected = trips_full[['route_id','shape_id','trip_id','start_stop_id', 'end_stop_id','num_stops', 'is_loop']]


	# id to human readeable info
	trips_full_s1 = trips_full_selected.merge(feed.stops, left_on='start_stop_id', right_on='stop_id', suffixes=('', '_'))
	trips_full_s1 = trips_full_s1[['route_id','shape_id','trip_id','stop_name', 'end_stop_id','num_stops', 'is_loop']]
	trips_full_s1.rename(columns={"stop_name": "origin_stop_name"}, inplace=True)

	trips_full_s2 = trips_full_s1.merge(feed.stops, left_on='end_stop_id', right_on='stop_id', suffixes=('', '_'))
	trips_full_s2 = trips_full_s2[['route_id','shape_id','trip_id','origin_stop_name', 'stop_name','num_stops', 'is_loop']]
	trips_full_s2.rename(columns={"stop_name": "destination_stop_name"}, inplace=True)

	trips_full_w_routes = trips_full_s2.merge(feed.routes, on='route_id')

	trips_full_w_agency = trips_full_w_routes.merge(feed.agency, on ='agency_id')

	trips_full_w_agency['route_mode'] = trips_full_w_agency['route_type'].apply(lambda x: route_type_to_mode(x))
	trips_full_w_agency['trip_name'] = trips_full_w_agency['route_id'] + "_" + trips_full_w_agency['trip_id'] 
	trips_full_w_agency['file_name'] = trips_full_w_agency['trip_name'].apply(lambda x: x.replace(' ','u').replace(':','u').replace('/','u'))

	# write outputs
	for id_, elem in trips_full_w_agency.iterrows():
		with open(os.path.join(working_directory.name, "{}.geojson".format(elem["file_name"])), 'w') as fp:
			as_geojson = feed_w_shapes.trip_to_geojson(elem["trip_id"], include_stops=True)
			as_geojson['features'][0]['properties'] = json.loads(elem.to_json())
			#put the stops in the right order
			stop_id_s_in_order = list(feed_w_shapes.stop_times[feed_w_shapes.stop_times["trip_id"]==elem["trip_id"]].sort_values(by=['stop_sequence'])['stop_id'])
			new_FeatureCollection = []
			new_FeatureCollection.append(as_geojson['features'][0])
			for stop_id in stop_id_s_in_order:
				feature = [elem for elem in as_geojson['features'] if elem['properties'].get('stop_id')==stop_id]
				new_FeatureCollection.append(feature[0])
			as_geojson['features'] = new_FeatureCollection
			json.dump(as_geojson, fp)
			

	trips_full_w_agency = trips_full_w_agency[['file_name','origin_stop_name', 'destination_stop_name','num_stops', 'is_loop', 'route_short_name', 'route_long_name', 'route_mode','route_color', 'agency_name', 'agency_url']]
	trips_full_w_agency.to_csv(os.path.join(working_directory.name, "trips.csv"))

	feed_w_shapes.stops.rename(columns={"stop_lat": "latitude"}, inplace=True)
	feed_w_shapes.stops.rename(columns={"stop_lon": "longitude"}, inplace=True)
	
	if "location_type" in feed_w_shapes.stops.columns:
		feed_w_shapes.stops.fillna({'location_type':0}, inplace=True)
		feed_w_shapes.stops['stop_type'] = feed_w_shapes.stops['location_type'].apply(lambda x: location_type_to_stop_type(x))
	else:
		feed_w_shapes.stops['stop_type'] = "stops"
	
	stop_types = feed_w_shapes.stops['stop_type'].unique()
	for stop_type_name in stop_types:
		stops = feed_w_shapes.stops[feed_w_shapes.stops['stop_type']==stop_type_name]
		stops.to_csv(os.path.join(working_directory.name, "{}.csv".format(stop_type_name)), float_format='%.6f')

	shutil.make_archive(output_file_name.split('.')[0], 'zip', working_directory.name)
	working_directory.cleanup()

if __name__ == '__main__':
	export_gtfs_as_geo("gtfs.zip", "output.zip")
