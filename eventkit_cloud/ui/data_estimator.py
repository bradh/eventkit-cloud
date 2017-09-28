from mapproxy import srs as mapproxy_srs
from mapproxy import grid as mapproxy_grid
from eventkit_cloud.jobs.models import ExportProvider
from django.core.exceptions import ObjectDoesNotExist
from string import Template
from django.conf import settings
from time import sleep

import requests
import json

def get_size_estimate(provider, bbox, srs='3857'):
    """
    Args:
        provider: The name of the provider, corresponds to the name field in Export Provider model
        bbox: A bbox in the format of an array
        srs: An EPSG code for the map being used.

    Returns: Estimated size in GB
    """
    try:
        provider = ExportProvider.objects.get(name=provider)
    except ObjectDoesNotExist:
        return None
    levels = range(provider.level_from, provider.level_to+1)
    req_srs = mapproxy_srs.SRS(srs)
    bbox = mapproxy_grid.grid_bbox(bbox, mapproxy_srs.SRS(4326), req_srs)

    tile_size = (256, 256)
    tile_grid = mapproxy_grid.TileGrid(srs, tile_size=tile_size, levels=len(levels))
    total_tiles = 0
    tiles = []
    for level in levels:
        # get_affected_level_tiles() returns a list with three
        # things: first a tuple with the bounding box, second
        # the height and width in tiles, and third a list of tile
        # coordinate tuples. result[1] gives the tuple with
        # the width/height of the desired set of tiles.
        result = tile_grid.get_affected_level_tiles(bbox, int(level))
        total_tiles += result[1][0] * result[1][1]
        tiles.append(result[1][0] * result[1][1])
    return [total_tiles, get_gb_estimate(total_tiles), tiles]


def get_gb_estimate(total_tiles, tile_width=256, tile_height=256):
    # the literal number there is the average pixels/GB ratio for tiles.
    gigs_per_pixel_constant = 0.0000000006
    return total_tiles*tile_width*tile_height*gigs_per_pixel_constant


def get_osm_feature_count(geojson_geometry=None):
    """
    :param geojson_geometry: this is a dict representing the geometry of a geojson feature 
    :return: the number of osm features contained in the geometry area
    """
    if settings.OVERPASS_API_URL:
        url = settings.OVERPASS_API_URL
    else:
        url = 'http://localhost/interpreter'
    verify_ssl = not getattr(settings, "DISABLE_SSL_VERIFICATION", False)
    if not geojson_geometry:
        raise Exception('A geojson geometry is required')

    if type(geojson_geometry is not dict):
        try:
            geojson_geometry = json.loads(geojson_geometry)
        except:
            raise Exception('Could not read passed in geojson geometry')

    if geojson_geometry['type'] == 'MultiPolygon':
        normal_coords = geojson_geometry['coordinates'][0][0]
    elif geojson_geometry['type'] == 'Polygon':
        normal_coords = geojson_geometry['coordinates'][0]
    else:
        raise  Exception('Geometry should be a polygon type')

    query_coords = reverse_polygon_lat_lon(normal_coords)
    query_coords = coord_array_to_string(query_coords)

    request_template = Template('[out:json];(node(poly:"$polygon");<;);out count;')

    query = request_template.safe_substitute(
        {'polygon': query_coords}
    )

    try:
        req = requests.post(settings.OVERPASS_API_URL, data=query, stream=False, verify=False)
    except requests.exceptions.RequestException as e:
        logger.error('Overpass query threw: {0}'.format(e))
        raise requests.exceptions.RequestException(e)

    if req.status_code == 429:
        while req.status_code == 429:
            print("We need to wait and try again")
            sleep(15)
            req = requests.post(url, data=query, stream=False, verify=verify_ssl)
    data = None
    try:
        data = json.loads(req.content)
    except:
        raise Exception('Could not parse response from OSM server')

    return data['elements'][0]['tags']['total'] or None

def reverse_polygon_lat_lon(coords):
    """
    :param coords: An array of coordinates. Example [[x,y][x,y][x,y][x,y]] 
    :return: An array of coordinates with x and y values swapped. [[y,x][y,x][y,x][y,x]]
    """
    if not coords:
        return None
    return [[coord[1], coord[0]]for coord in coords]

def coord_array_to_string(coords_array):
    """
    :param coords_array: An array of coords in the form of [[a,b],[a,b],[a,b]] 
    :return: A string representing the coordinates in the array separated by spaces
    """
    if not(coords_array):
        return None
    return_string = ''
    for coord in coords_array:
        return_string += '{0} {1} '.format(coord[0], coord[1])
    return return_string.rstrip(' ')