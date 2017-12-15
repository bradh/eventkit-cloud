# -*- coding: utf-8 -*-
import logging

from django.test import TestCase

from ..data_estimator import get_size_estimate, get_gb_estimate, get_osm_feature_count, \
    make_osm_feature_request, reverse_polygon_lat_lon, coord_array_to_string
from requests.exceptions import RequestException
from mock import Mock, patch
import json

logger = logging.getLogger(__name__)


class TestDataEstimation(TestCase):

    def test_get_gb_estimate(self):
        expected_return_value = 0.0001572864
        actual_return_value = get_gb_estimate(4)
        self.assertAlmostEqual(expected_return_value, actual_return_value, places=9)

    @patch('eventkit_cloud.ui.data_estimator.get_gb_estimate')
    @patch('eventkit_cloud.ui.data_estimator.DataProvider')
    def test_get_size_estimate(self, export_provider, get_estimate):
        provider_name = "Test_name"
        get_estimate.return_value = 4
        export_provider.objects.get.return_value = Mock(level_from=0, level_to=1)
        returned_values = get_size_estimate(provider_name, bbox=[-1, -1, 0, 0])
        export_provider.objects.get.assert_called_once_with(name=provider_name)
        # two tiles, an arbritary value of four from the mock, one tile per level represented in array.
        expected_values = [2, 4, [1, 1]]
        self.assertEquals(returned_values, expected_values)

    @patch('eventkit_cloud.ui.data_estimator.make_osm_feature_request')
    def test_get_osm_feature_count(self, make_request):
        make_request.return_value = 44

        with self.assertRaises(Exception):
            count = get_osm_feature_count(geojson_geometry=None)

        with self.assertRaises(Exception):
            count = get_osm_feature_count(geojson_geometry='not a dict object')

        point_geometry = "{\
            'type': 'Point',\
            'coordinates': [1, 1]\
        }"

        with self.assertRaises(Exception):
            count = get_osm_feature_count(geojson_geometry=point_geometry)

        multipolygon = {
            "type": "MultiPolygon",
            "coordinates": [
              [[
                [-43, 30],
                [-17, 30],
                [-17, 45],
                [-43, 45],
                [-43, 30]
              ]],
              [[
                [0, 31],
                [24, 31],
                [24, 46],
                [0, 46],
                [0, 31]
              ]]
            ]
        }

        count = get_osm_feature_count(geojson_geometry=multipolygon)
        self.assertEqual(count, 88)

        polygon = {
            "type": "Polygon",
            "coordinates": [
              [
                [-43, 30],
                [-17, 30],
                [-17, 45],
                [-43, 45],
                [-43, 30]
              ]
            ]
        }

        count = get_osm_feature_count(geojson_geometry=polygon)
        self.assertEqual(count, 44)

    @patch('eventkit_cloud.ui.data_estimator.sleep')
    @patch('eventkit_cloud.ui.data_estimator.requests.post')
    def test_make_osm_feature_request(self, mock_post, mock_sleep):
        with self.assertRaises(Exception):
            count = make_osm_feature_request()

        with self.settings(
                OVERPASS_API_URL='http://my-overpass/interpreter',
                DISABLE_SSL_VERIFICATION=True
        ):
            coords = '30 -43 30 -17 45 -17 45 -43 30 -43'
            expected_query = '[out:json];(node(poly:"{0}");<;);out count;'.format(coords)
            expected_content = {'elements' : [{'tags': {'total': 44}}]}
            mock_response = Mock()
            mock_response.content = json.dumps(expected_content)
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            count = make_osm_feature_request(query_coords=coords)
            self.assertEqual(count, 44)
            mock_post.assert_called_once_with('http://my-overpass/interpreter',
                                              data=expected_query,
                                              stream=False,
                                              verify=False)

            expected_content = {'elements': [{'count': {'total': 33}}]}
            mock_response.content = json.dumps(expected_content)
            mock_post.return_value = mock_response
            count = make_osm_feature_request(query_coords=coords)
            self.assertEqual(count, 33)

            mock_response.content = 'not a dict object'
            count = make_osm_feature_request(query_coords=coords)
            self.assertEquals(count, 0)

            mock_post.side_effect = RequestException()
            with self.assertRaises(RequestException):
                count = make_osm_feature_request(query_coords=coords)

            mock_response.content = {}
            mock_response.status_code = 429
            mock_post.side_effect = None
            mock_post.return_value = mock_response
            self.assertEqual(mock_sleep.call_count, 0)
            count = make_osm_feature_request(query_coords=coords)
            self.assertEqual(count, 0)
            self.assertEqual(mock_sleep.call_count, 10)

    def test_reverse_polygon_lat_lon(self):
        coords = [[1, 2], [3, 4], [5, 6], [7, 8]]
        expected_coords = [[2, 1], [4, 3], [6, 5], [8, 7]]
        result = reverse_polygon_lat_lon(coords)
        self.assertEqual(result, expected_coords)

        self.assertEqual(reverse_polygon_lat_lon(None), None)

    def test_coord_array_to_string(self):
        coords = [[2, 1], [4, 3], [6, 5], [8, 7]]
        expected_string = '2 1 4 3 6 5 8 7'
        result = coord_array_to_string(coords)
        self.assertEqual(result, expected_string)

        self.assertEqual(coord_array_to_string(None), None)