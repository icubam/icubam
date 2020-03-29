import numpy as np
import tornado.web

from bokeh.embed import components
from bokeh.plotting import figure
from icubam.www.handlers import base


class PlotHandler(base.BaseHandler):
  ROUTE = '/plot'

  def initialize(self, config, db):
    super().initialize(config, db)
    self.db = db

  @tornado.web.authenticated
  async def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    data = {}
    figures = []

    for _ in range(3):
      x = [i for i in range(10)]
      y = np.random.random(10)

      p = figure(plot_width=800, plot_height=250, x_axis_type="datetime")
      p.line(x, y, color='navy', alpha=0.5)

      script, div = components(p)
      figures.append(dict(script=script, div=div))

    self.render("plot.html", figures=figures)
