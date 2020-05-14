import os
import tempfile
import urllib.request
import pathlib

import bottle

from lib.gtfs_geo import export_gtfs_as_geo

app = bottle.default_app()

@app.get('/api', methods=['GET'])
def gtfs_geo_api():
	gtfs_url = bottle.request.params.get('gtfs_url')

	if gtfs_url:
		file_name, file_path = download_gtfs_file(gtfs_url)
	else:
		bottle.abort(400)

	return create_gtfs_geo_file(file_path, 'gtfs_geo_output.zip')

def download_gtfs_file(url):
	file_name = tempfile.mktemp(suffix=pathlib.Path(url).name)
	file_path, headers = urllib.request.urlretrieve(url, filename=file_name)
	return pathlib.Path(url).name, file_path

def create_gtfs_geo_file(gtfs_file_path, output_name):
	export_gtfs_as_geo(gtfs_file_path, output_name)

	return bottle.static_file(
		output_name,
		root = ".",
		download = output_name,
		mimetype = 'application/zip')

if __name__ == '__main__':
    bottle.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=True)
