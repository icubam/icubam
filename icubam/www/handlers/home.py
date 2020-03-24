import collections
import json
import os.path
import tornado.web
import tornado.template
from icubam.www.handlers import base
from icubam import config


def get_color(value):
  color = 'red'
  if value < 0.5:
    color = 'greed'
  elif value < 0.8:
    color = 'orange'
  return color


class HomeHandler(base.BaseHandler):

  ROUTE = '/'
  POPUP_TEMPLATE = 'popup.html'
  CLUSTER_KEY = 'dept'  # city

  def initialize(self, db):
    self.db = db
    loader = tornado.template.Loader(self.get_template_path())
    self.popup_template = loader.load(self.POPUP_TEMPLATE)

  def get_city_data(self):
    icus_df = self.db.get_icus()
    coords = dict()
    cluster_id = dict()  # the city for each icu
    for city, rows in icus_df.groupby(self.CLUSTER_KEY):
      coords[city] = {'lat': rows.lat.mean(), 'lng': rows.long.mean()}
      for icuid in rows.icu_id.to_list():
        cluster_id[icuid] = city
    return coords, cluster_id

  def get_phones(self):
    users_df = self.db.get_users()
    result = collections.defaultdict(list)
    for index, row in users_df.iterrows():
      result[row.icu_id].append(row.telephone)
    return result

  def get_beds_per_city(self, df, phones: dict, cluster_id: dict):
    result = collections.defaultdict(list)
    for index, row in df.iterrows():
      city = cluster_id.get(row.icu_id, None)
      if city is None:
        logging.error('Did not find a city for ICU {}'.format(row.icu_id))
        continue

      occupied_ratio = row.n_covid_free / row.total
      result[city].append({
        'icu': row.icu_name,
        'phone': phones.get(row.icu_id, [''])[0],
        'free': int(row.n_covid_free),
        'total': int(row.total),
        'occupation': occupied_ratio,
        'color': get_color(occupied_ratio)
      })

    return result

  @tornado.web.authenticated
  def get(self):
    coords, cluster_id = self.get_city_data()
    phones = self.get_phones()
    df = self.db.get_bedcount()
    df['total'] = df.n_covid_free.astype(int) + df.n_covid_occ.astype(int)
    beds_per_city = self.get_beds_per_city(df, phones, cluster_id)

    print(list(coords.keys()))

    data = []
    for city, beds in beds_per_city.items():
      occupations = [x['occupation'] for x in beds]
      occupation = sum(occupations) / len(occupations)
      color = get_color(occupation)
      latlng = coords.get(city, None)
      if not latlng:
        logging.error(f'Could not find location for {city}')
        continue

      data.append({
        'id': 'id_{}'.format(city.replace(' ', '_')),
        'label': city,
        'lat': latlng['lat'],
        'lng': latlng['lng'],
        'color': color,
        'popup': self.popup_template.generate(beds=beds).decode()
      })

    self.render("index.html", API_KEY=config.GOOGLE_API_KEY, data=json.dumps(data))
