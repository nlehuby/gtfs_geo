import argparse

from lib.gtfs_geo import export_gtfs_as_geo

def cli():
	parser = argparse.ArgumentParser(
		prog = "gtfs_geo",
		description="Export geographical files from a GTFS feed")
	parser.add_argument("gtfs_file", nargs=1,
		help='a valid GTFS feed (zip file)')
	parser.add_argument("output_file", nargs="?",
		default="gtfs_geo_output.zip",
		help='a name for the output zip file')
	args = parser.parse_args()

	print(">>> launching")
	gtfs_file_path = args.gtfs_file[0]

	export_gtfs_as_geo(gtfs_file_path, args.output_file)

if __name__ == '__main__':
	cli()
