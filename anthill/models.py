from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import simplejson
import urllib

def _geocode(location):
    """
        Given a location return a ``Point``, name pair.
    """
    params = {
     'q': location,
     'key': settings.ANTHILL_GMAPS_KEY,
     'sensor': 'false',
     'output': 'json',
    }
    url = 'http://maps.google.com/maps/geo?%s' % urllib.urlencode(params)

    try:
        resp = urllib.urlopen(url).read()
        resp = simplejson.loads(resp)
        if resp['Status']['code'] == 200:
            pmark = resp['Placemark'][0]
            lon,lat = pmark['Point']['coordinates'][0:2]
            return Point(lat, lon), pmark['address']
        else:
            return None, None
    except:
        return None, None

class LocationModelQuerySet(models.query.GeoQuerySet):
    """ GeoQuerySet augmented with a search_by_distance method """

    def search_by_distance(self, location, mile_radius):
        point, location_name = _geocode(location)
        if point:
            result = self.filter(lat_long__distance_lte=(point, D(mi=mile_radius))).distance(point).order_by('distance')
        else:
            result = self
        result.geocoded_location = location_name
        return result

class LocationModelManager(models.GeoManager):
    """ Manager for LocationModels to use LocationModelQuerySet """

    def get_query_set(self):
        return LocationModelQuerySet(self.model)

class LocationModel(models.Model):
    """
        Serves as an Abstract Base Model for Events and Profiles

        Provides child models with locations in both string form (``location``)
        and an automatically-geocoded lat_long field.  QuerySets also grow a
        ``search_by_distance`` method.
    """
    location = models.CharField('description of location, hopefully geocodable (eg. Washington, DC)', max_length=100, blank=True)
    lat_long = models.PointField('geocoded location', null=True, blank=True)

    objects = LocationModelManager()

    def save(self, *args, **kwargs):
        if self.location:
            self.lat_long, _ = _geocode(self.location)
        super(LocationModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True
