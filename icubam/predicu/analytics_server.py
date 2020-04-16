import os

from absl import logging  # noqa: F401
from icubam.predicu.plot import generate_plots
from icubam.config import Config
from icubam.db.store import to_pandas


class AnalyticsCallback:
  def __init__(self, config: Config, db_factory):
    self.config = config
    self.db_factory = db_factory

  async def generate_plots(self):
    db = self.db_factory.create()
    data = to_pandas(db.get_bed_counts())
    logging.info('[periodic callback] Starting plots generation with predicu')
    generate_plots(
      bedcounts_data=data, output_dir=self.config.backoffice.extra_plots_dir
    )


def register_analytics_callback(config: Config, db_factory, ioloop) -> None:
  """Register a callback to generate plots"""
  extra_plots_dir = config.backoffice.extra_plots_dir
  repeat_every = config.backoffice.extra_plots_make_every * 1000
  if repeat_every <= 0:
    logging.warn(
      f"analytics callback not started, as extra_plots_make_every={repeat_every}"
    )

  if (
    not os.path.isdir(extra_plots_dir) and
    not os.path.isdir(os.path.dirname(extra_plots_dir))
  ):
    logging.warn(
      f'predicu plots not generated, as extra_plots_dir '
      f'is not valid directory: {extra_plots_dir}'
    )
  else:
    logging.info(
      f"Registering periodic callback: generate_predicu_plots "
      f"/{repeat_every/1000}s"
    )
    callback = AnalyticsCallback(config, db_factory)
    ioloop.PeriodicCallback(callback.generate_plots, repeat_every).start()
