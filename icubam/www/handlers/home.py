import tornado.web
from icubam.www.handlers import base


class HomeHandler(base.BaseHandler):

  ROUTE = '/'

  def initialize(self, db):
    self.db = db

  @tornado.web.authenticated
  def get(self):
    # Retrieves lat-longs
    icus_df = self.db.get_icus()
    latlngs = dict()
    for index, row in icus_df.iterrows():
      latlngs[row.icu_id] = (row.lat, row.long)

    beds_df = self.db.get_bedcount()
    data = []
    for index, row in beds_df.iterrows():
      coords = latlngs.get(row.icu_id, None)
      if coords is None:
        continue

      total = int(row.n_covid_free) + int(row.n_covid_occ)
      data.append({
        'id': "icu_{}".format(row.icu_id),
        'label': row.icu_name,
        'free_beds': int(row.n_covid_free),
        'total_beds': total,
        'lat': coords[0],
        'lng': coords[1],
        'radius': total,
      })

    self.render("index.html", data=data)
