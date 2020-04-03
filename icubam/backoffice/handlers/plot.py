import numpy as np
import tornado.web
import math
from collections import defaultdict

from bokeh.embed import components
from bokeh.plotting import figure
from icubam.backoffice.handlers import base

from pprint import pprint


class PlotHandler(base.BaseHandler):
  ROUTE = '/plot'

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    figures = []

    bed_counts = self.db.get_visible_bed_counts_for_user(self.user.user_id)
    cities = defaultdict(int)
    for curr in bed_counts:
      cities[curr.icu.city] += curr.n_covid_free

    get_val = lambda tup: tup[1]
    cities = list(cities.items())
    cities.sort(key=get_val, reverse=True)

    cities_names, beds_available  = zip(*cities)
    max_val = max(cities, key=get_val)

    p = figure(
      x_range=cities_names,
      plot_height=400,
      title="Lits Disponibles Par Ville"
    )
    p.xaxis.major_label_orientation = math.pi / 2
    p.y_range.start = 0

    p.vbar(x=cities_names, top=beds_available, width=0.9)

    script, div = components(p)
    figures.append(dict(script=script, div=div))

    self.render("plot.html", figures=figures)
