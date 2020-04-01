import numpy as np
import tornado.web
import math

from bokeh.embed import components
from bokeh.plotting import figure
from icubam.www.handlers import base

from pprint import pprint

class PlotHandler(base.BaseHandler):
  ROUTE = '/plot'

  def initialize(self, config, db):
    super().initialize(config, db)

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    data = {}
    figures = []

    # plot
    # bed_counts = self.db.get_bed_counts()
    bed_counts = self.db.get_visible_bed_counts_for_user(None, force=True)
    cities = {}
    for curr in bed_counts:
      curr = curr.to_dict()
      city_name = curr['icu']['city']
      val = cities.get(city_name, 0)
      val += curr['n_covid_free']
      cities[city_name] = val

    get_val = lambda tup: tup[1]
    cities = [(name, val) for name, val in cities.items()]
    cities.sort(key=get_val, reverse=True)

    cities_names = [name for name, _ in cities]
    max_val = max(cities, key=get_val)
    beds_available = [val for _, val in cities]

    p = figure(
      x_range=cities_names,
      plot_height=400,
      title="Lits Disponibles Par Ville")
    p.xaxis.major_label_orientation = math.pi/2
    p.y_range.start = 0

    p.vbar(x=cities_names, top=beds_available, width=0.9)

    script, div = components(p)
    figures.append(dict(script=script, div=div))
    # for i, el in enumerate(bed_counts):
    #   pprint(el.to_dict())
    #   if i > 3:
    #     break



    # for _ in range(3):
    #   x = [i for i in range(10)]
    #   y = np.random.random(10)

    #   p = figure(plot_width=800, plot_height=250, x_axis_type="datetime")
    #   p.line(x, y, color='navy', alpha=0.5)

      # script, div = components(p)
      # figures.append(dict(script=script, div=div))

    self.render("plot.html", figures=figures)