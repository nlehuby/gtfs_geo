# GTFS → geo

Turn a GTFS feed to geo info (csv and geojson files)

![logo](gtfs_geo/gtfs_geo.png)

[Try it out](https://gtfs-geo.herokuapp.com/)

## cli usage
In addition to the web interface, a python command line interface is also available to test on local GTFS files:

```
$ python cli.py --help
usage: gtfs_geo [-h] gtfs_file [output_file]

Export geographical files from a GTFS feed

positional arguments:
  gtfs_file    a valid GTFS feed (zip file)
  output_file  a name for the output zip file

optional arguments:
  -h, --help   show this help message and exit

```
