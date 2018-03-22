from django.conf import settings
from django.core.cache import cache
import logging
import requests
import json

logger = logging.getLogger(__name__)

def getAuthHeaders():
    if getattr(settings, 'GEOCODING_AUTH_URL') is not None:
        if cache.get('pelias_token') is None: 
            self.authenticate()
        return { 'Authorization' : 'Bearer ' + str(cache.get('pelias_token')) }
    else:
        return {}

def authenticate():
    logger.info('Receiving new authentication token for geocoder')
    try: 
        authResponse = requests.get(getattr(settings, 'GEOCODING_AUTH_URL'))
        cache.set('pelias_token', authResponse.json()['access_token'], None)
        return self
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return