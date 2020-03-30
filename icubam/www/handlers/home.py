from absl import logging
import collections
import json
import os.path
import tornado.web
import tornado.template
from icubam.www.handlers import base
from icubam.www import token
from icubam import config


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
  CLUSTER_KEY = 'dept'  # city

  def initialize(self, config, db):
    super().initialize(config, db)
    loader = tornado.template.Loader(self.get_template_path())
    self.token_encoder = token.TokenEncoder(self.config)
    self.popup_template = loader.load(self.POPUP_TEMPLATE)
    self.icus_df = self.db.get_icus()

  def get_city_data(self):
    coords = dict()
    cluster_id = dict()  # the city for each icu
    for city, rows in self.icus_df.groupby(self.CLUSTER_KEY):
      coords[city] = {'lat': rows.lat.mean(), 'lng': rows.long.mean()}
      for icuid in rows.icu_id.to_list():
        cluster_id[icuid] = city
    return coords, cluster_id

  def get_phones(self):
    result = collections.defaultdict(list)
    for index, row in self.icus_df.iterrows():
      result[row['icu_id']].append(row['telephone'])
    return result

  def get_beds_per_city(self, df, phones: dict, cluster_id: dict):
    result = collections.defaultdict(list)
    for index, row in df.iterrows():
      city = cluster_id.get(row.icu_id, None)
      if city is None:
        logging.error('Did not find a city for ICU {}'.format(row.icu_id))
        continue

      total = int(row['total'])
      occupied_ratio = int(row.n_covid_occ) / total if (total > 0) else 0
      result[city].append({
        'icu': row['icu_name'],
        'phone': str(phones.get(row['icu_id'], [''])[0]).lstrip('+'),
        'occ': int(row['n_covid_occ']),
        'free': int(row['n_covid_free']),
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

    df = self.icus_df
    icu = df[df.icu_id == icu_data['icu_id']].to_dict(orient='records')
    if not icu:
      return None

    return {'lat': icu[0].get('lat', None), 'lng': icu[0].get('long', None)}

  @tornado.web.authenticated
  def get(self):
    coords, cluster_id = self.get_city_data()
    phones = self.get_phones()
    df = self.db.get_bedcount()
    df['total'] = df.n_covid_free.astype(int) + df.n_covid_occ.astype(int)
    beds_per_city = self.get_beds_per_city(df, phones, cluster_id)
    data = []
    for city, beds in beds_per_city.items():
      cluster = {'city': city, 'icu': city, 'phone': None}
      for key in ['occ', 'free', 'total', 'ratio']:
        cluster[key] = sum([x[key] for x       in beds])
      cluster['ratio'] =  cluster['ratio'] / len(beds)
      cluster['color'] = get_color(cluster['ratio'])
      latlng = coords.get(city, None)
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
