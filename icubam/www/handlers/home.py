from absl import logging
import collections
import json
import os.path
import tornado.web
import tornado.template
from typing import List, Dict
from icubam.www.handlers import base
from icubam.www import token
from icubam import config
from icubam.db import store


def get_color(value):
  color = 'red'
  if value < 0.5:
    color = 'green'
  elif value < 0.8:
    color = 'orange'
  return color


class HomeHandler(base.BaseHandler):

  ROUTE = '/'
  POPUP_TEMPLATE = 'popup.html'
  # TODO(olivier): put this in the config
  CLUSTER_KEY = 'dept'  # city

  def initialize(self, config, db):
    super().initialize(config, db)
    loader = tornado.template.Loader(self.get_template_path())
    self.token_encoder = token.TokenEncoder(self.config)
    self.popup_template = loader.load(self.POPUP_TEMPLATE)

  def groupby(self):
    result = collections.defaultdict(list)
    for icu in self.icus.values():
      icu_dict = store.to_dict(icu)
      key = icu_dict.get(self.CLUSTER_KEY, None)
      if key is None:
        logging.error('icu {} has no {}'.format(icu.icu_id, self.CLUSTER_KEY))
        continue
      result[key].append(icu_dict)
    return result

  def get_mean_coords(self, icus: List[Dict]):
    result = {'lat': 0.0, 'lng': 0.0}
    cnt = 0
    for icu in icus:
      lat = icu.get('lat', None)
      lng = icu.get('long', None)
      if lat is not None and lng is not None:
        cnt += 1
        result['lat'] += lat
        result['lng'] += lng
    if cnt > 0:
      result['lat'] /= cnt
      result['lng'] /= cnt
    return result

  def get_coords(self):
    result = dict()
    for city, icus in self.groupby().items():
      result[city] = self.get_mean_coords(icus)
    return result

  def get_beds_per_city(self, bedcounts):
    result = collections.defaultdict(list)
    for bedcount in bedcounts:
      icu = self.icus.get(bedcount.icu_id, None)
      if icu is None:
        logging.error('No ICU {} for this bedcount'.format(bedcount.icu_id))
        continue

      cluster_id = getattr(icu, self.CLUSTER_KEY)
      if cluster_id is None:
        logging.error('Did not find a {} for ICU {}'.format(
          self.CLUSTER_ID, icu.icu_id))
        continue

      covid_occ = 0 if bedcount.n_covid_occ is None else bedcount.n_covid_occ
      covid_fre = 0 if bedcount.n_covid_free is None else bedcount.n_covid_free
      phone = '' if icu.telephone is None else icu.telephone
      total = covid_occ + covid_fre
      occupied_ratio = covid_occ / total if (total > 0) else 0
      result[cluster_id].append({
        'icu': icu.name,
        'phone': phone.lstrip('+'),
        'occ': covid_occ,
        'free': covid_fre,
        'total': total,
        'ratio': occupied_ratio,
        'color': get_color(occupied_ratio)
      })
    return result

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
    bedcounts = self.db.get_bed_counts()
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
                version=self.config.version)
