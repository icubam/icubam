import numpy as np
import tornado.web
import math
from collections import defaultdict

from bokeh.embed import components
from bokeh.plotting import figure
from icubam.backoffice.handlers import base

from pprint import pprint


class OperationalDashHandler(base.BaseHandler):
  ROUTE = '/operational-dashboard'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    arg_region = self.get_query_argument('region', default=None)

    current_region = None
    current_region_name = "Toutes les régions"
    if arg_region is not None and arg_region.isdigit():
      try:
        current_region = self.db.get_region(int(arg_region))
        current_region_name = current_region.name
      except Exception:
        logging.warning(
          f"Invalid query argument: region={arg_region} "
          f"Falling back to all regions."
        )

    figures = []

    bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)
    if current_region is not None:
      # TODO: filter in DB query
      bed_counts = [
        el for el in bed_counts if el.icu.region_id == current_region.region_id
      ]
    cities = defaultdict(int)
    for curr in bed_counts:
      cities[curr.icu.city] += curr.n_covid_free

    get_val = lambda tup: tup[1]
    cities = list(cities.items())
    cities.sort(key=get_val, reverse=True)

    if len(cities):
      cities_names, beds_available = zip(*cities)
    else:
      cities_names, beds_available = [], []

    p = figure(
      x_range=cities_names,
      plot_height=400,
      sizing_mode="stretch_width",
      title="Lits Disponibles Par Ville"
    )
    p.xaxis.major_label_orientation = math.pi / 4
    p.y_range.start = 0

    p.vbar(x=cities_names, top=beds_available, width=0.9)

    script, div = components(p)
    figures.append(dict(script=script, div=div))

    regions = [{
      'name': el.name,
      'id': el.region_id
    } for el in self.db.get_regions()]
    regions = list(sorted(regions, key=lambda x: x['name']))

    self.render(
      "operational-dashboard.html",
      figures=figures,
      regions=regions,
      current_region_name=current_region_name
    )
