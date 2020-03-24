import os.path
import json
import tornado.web
import tornado.template
from icubam.www.handlers import base
from icubam import config


def get_color(row):
  occupation = row.n_covid_free / row.total
  color = 'green'
  if occupation > 0.8:
    color = 'red'
  elif occupation > 0.5:
    color = 'orange'
  return color


class HomeHandler(base.BaseHandler):

  ROUTE = '/'
  POPUP_TEMPLATE = 'popup.html'

  def initialize(self, db):
    self.db = db
    loader = tornado.template.Loader(self.get_template_path())
    self.popup_template = loader.load(self.POPUP_TEMPLATE)

  @tornado.web.authenticated
  def get(self):
    # Retrieves lat-longs
    icus_df = self.db.get_icus()
    latlngs = dict()
    for index, row in icus_df.iterrows():
      latlngs[row.icu_id] = (row.lat, row.long)

    df = self.db.get_bedcount()
    df['total'] = df.n_covid_free.astype(int) + df.n_covid_occ.astype(int)
    data = []
    for index, row in df.iterrows():
      coords = latlngs.get(row.icu_id, None)
      if coords is None:
        continue

      color = get_color(row)
      data.append({
        'id': "icu_{}".format(row.icu_id),
        'label': row.icu_name,
        'lat': coords[0],
        'lng': coords[1],
        'color': color,
        'popup': self.popup_template.generate(row=row, color=color).decode()
      })

    self.render("index.html", API_KEY=config.GOOGLE_API_KEY, data=json.dumps(data))
