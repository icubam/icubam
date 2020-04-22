from pathlib import Path

from absl import logging  # noqa: F401

from icubam.config import Config
from icubam.db.store import to_pandas
from icubam.predicu.preprocessing import preprocess_bedcounts
from icubam.predicu.plot import generate_plots


class AnalyticsCallback:
  def __init__(self, output_dir, db_factory):
    self.output_dir = output_dir
    self.db_factory = db_factory

  async def generate_plots(self):
    db = self.db_factory.create()
    df_bedcounts = to_pandas(db.get_bed_counts())
    df_bedcounts = preprocess_bedcounts(df_bedcounts)
    logging.info('[periodic callback] Starting plots generation with predicu')
    cached_data = {'bedcounts': df_bedcounts}
    generate_plots(
      plots=["flux_dept_lits_dept_visu_4panels"],
      cached_data=cached_data,
      output_dir=self.output_dir
    )
    logging.info('[periodic callback] Finished plots generation with predicu')


def register_analytics_callback(config: Config, db_factory, ioloop) -> None:
  """Register a callback to generate plots"""
  extra_plots_dir = config.backoffice.extra_plots_dir
  if extra_plots_dir is not None:
    extra_plots_dir = Path(extra_plots_dir)

  if config.backoffice.extra_plots_make_every <= 0:
    logging.warn(
      f"analytics callback not started, as extra_plots_make_every"
      f"={config.backoffice.extra_plots_make_every}"
    )
    return
  repeat_every = config.backoffice.extra_plots_make_every * 1000

  if (
    extra_plots_dir is None or
    not (extra_plots_dir.exists() or extra_plots_dir.parent.exists())
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
    callback = AnalyticsCallback(config.backoffice.extra_plots_dir, db_factory)
    ioloop.PeriodicCallback(callback.generate_plots, repeat_every).start()
