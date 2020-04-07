from absl import logging
import collections
import json
import tornado.web
from typing import List, Dict
import icubam
from icubam.www.handlers import base
from icubam.www import token
from icubam import map_builder



class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.builder = map_builder.MapBuilder(
      config, db_factory, 'www/templates/index.html')
    self.token_encoder = token.TokenEncoder(self.config)
    self.popup_template = loader.load(self.POPUP_TEMPLATE)

  
  def center_map(self):
    icu_data = self.token_encoder.decode(self.get_secure_cookie(self.COOKIE))
    if icu_data is None:
      logging.error('Cookie cannot be decoded.')
      return None

    icu = self.icus.get(icu_data['icu_id'], None)
    if icu is None:
      logging.error('No such ICU {}'.format(icu_data['icu_id']))
      return None

    return {'lat': icu.lat, 'lng': icu.long}

  @tornado.web.authenticated
  def get(self):
    self.icus = {x.icu_id: x for x in self.db.get_icus()}
    city_coords = self.get_coords()
    # TODO(olivier): pass the user here!
    bedcounts = self.db.get_visible_bed_counts_for_user(None, force=True)
    beds_per_city = self.get_beds_per_city(bedcounts)
    data = []
    for city, beds in beds_per_city.items():
      cluster = {'city': city, 'icu': city, 'phone': None}
      for key in ['occ', 'free', 'total', 'ratio']:
        cluster[key] = sum([x[key] for x in beds])
      cluster['ratio'] =  cluster['ratio'] / len(beds)
      cluster['color'] = get_color(cluster['ratio'])
      latlng = city_coords.get(city, None)
      if not latlng:
        logging.error(f'Could not find location for {city}')
        continue

      views = [
        {'name': 'cluster', 'beds': [cluster]},
        {'name': 'full', 'beds': sorted(beds, key=lambda x: x['icu'])},
      ]
      popup = self.popup_template.generate(
        cluster=cluster['city'], color=cluster['color'], views=views)

      data.append({
        'id': 'id_{}'.format(city.replace(' ', '_')),
        'label': city,
        'lat': latlng['lat'],
        'lng': latlng['lng'],
        'color': cluster['color'],
        'free': str(cluster['free']),
        'popup': popup.decode(),
      })

    # This sorts the from north to south, so as to avoid overlap on the north.
    data.sort(key=lambda x: x['lat'], reverse=True)
    center = self.center_map()
    self.render("index.html",
                API_KEY=self.config.GOOGLE_API_KEY,
                center=json.dumps(center),
                data=json.dumps(data),
                version=icubam.__version__)


class MapByAPIHandler(HomeHandler):
  """Same as HomeHandler but accessed with an API KEY"""

  ROUTE = '/map'

  def get_current_user(self):
    key = self.get_query_argument('API_KEY', None)
    if key is None:
      return

    return self.db.auth_external_client(key)
