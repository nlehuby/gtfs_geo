import json
import os
import tempfile
import shutil

import gtfstk

def export_gtfs_as_geo(input_gtfs_file, output_file_name):
	working_directory = tempfile.TemporaryDirectory()
	feed = gtfstk.read_gtfs(input_gtfs_file, dist_units='km')

	feed_w_shapes = gtfstk.miscellany.create_shapes(feed)

	# keep only a relevant subset 
	feed_w_shapes_selected = feed_w_shapes.trips[['route_id', 'direction_id', 'shape_id', 'trip_id']]
	feed_w_shapes_dedup = feed_w_shapes_selected.drop_duplicates(subset=['route_id', 'direction_id', 'shape_id'])

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

	# TODO - route_type

	trips_full_w_agency['trip_name'] = trips_full_w_agency['route_id'] + "_" + trips_full_w_agency['trip_id'] 
	trips_full_w_agency['file_name'] = trips_full_w_agency['trip_name'].apply(lambda x: x.replace(' ','u').replace(':','u').replace('/','u'))

	# write outputs
	for id_, elem in trips_full_w_agency.iterrows():
		with open(os.path.join(working_directory.name, "{}.geojson".format(elem["file_name"])), 'w') as fp:
			json.dump(feed_w_shapes.trip_to_geojson(elem["trip_id"], include_stops=True), fp)

	trips_full_w_agency = trips_full_w_agency[['file_name','origin_stop_name', 'destination_stop_name','num_stops', 'is_loop', 'route_short_name', 'route_long_name', 'route_type','route_color', 'agency_name', 'agency_url']]
	trips_full_w_agency.to_csv(os.path.join(working_directory.name, "trips.csv"))

	feed_w_shapes.stops.rename(columns={"stop_lat": "latitude"}, inplace=True)
	feed_w_shapes.stops.rename(columns={"stop_lon": "longitude"}, inplace=True)
	feed_w_shapes.stops.to_csv(os.path.join(working_directory.name, "stops.csv"))

	shutil.make_archive(output_file_name.split('.')[0], 'zip', working_directory.name)
	working_directory.cleanup()

if __name__ == '__main__':
	export_gtfs_as_geo("gtfs.zip", "output.zip")
