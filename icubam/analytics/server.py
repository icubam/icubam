import numbers
import tornado.ioloop

from icubam import base_server, sentry
from icubam.analytics import generator, dataset
from icubam.analytics.handlers import dataset as dataset_handler


class AnalyticsServer(base_server.BaseServer):
  """Runs analytics jobs."""
  def __init__(self, config, port):
    super().__init__(config, port)
    self.port = port if port is not None else self.config.analytics.port
    self.db = self.db_factory.create()
    sentry.maybe_init_sentry(config, server_name='analytics')

    # Periodic data generation and cache have the same frequency.
    frequency = config.analytics.generate_plots_every
    if not isinstance(frequency, numbers.Number) or frequency <= 0:
      frequency = None
    self.dataset = dataset.Dataset(self.db, ttl=frequency - 1)
    self.generator = generator.PlotGenerator(
      self.config, self.db, self.dataset, frequency
    )
    self.generator.register(tornado.ioloop)

  def make_app(self):
    self.add_handler(
      dataset_handler.DatasetHandler,
      config=self.config,
      db_factory=self.db_factory,
      dataset=self.dataset
    )
    # Only accepts request from same host
    app_routes = [
      (tornado.routing.HostMatches(r'(localhost|127\.0\.0\.1)'), self.routes)
    ]
    return tornado.web.Application(app_routes)
