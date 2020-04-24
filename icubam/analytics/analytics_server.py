from pathlib import Path

from absl import logging  # noqa: F401

from icubam.analytics import data, plots
from icubam.config import Config


class AnalyticsCallback:
  def __init__(self, output_dir, db_factory):
    self.output_dir = output_dir
    self.db_factory = db_factory

  async def generate_plots(self):
    df_bedcounts = data.load_bed_counts(
      self.db_factory.create(), preprocess=True
    )
    logging.info('[periodic callback] Starting plots generation with predicu')
    plot_data = {'bedcounts': df_bedcounts}
    plots.generate_plots(
      plots=["flux_dept_lits_dept_visu_4panels"],
      data=plot_data,
      output_dir=self.output_dir
    )
    logging.info('[periodic callback] Finished plots generation with predicu')


def register_analytics_callback(config: Config, db_factory, ioloop) -> None:
  """Register a callback to generate plots"""
  extra_plots_dir = config.backoffice.extra_plots_dir
  if extra_plots_dir is not None:
    extra_plots_dir = Path(extra_plots_dir)

  if config.backoffice.extra_plots_make_every <= 0:
    logging.warning(
      f"Analytics callback not started, as extra_plots_make_every"
      f"={config.backoffice.extra_plots_make_every}"
    )
    return
  repeat_every = config.backoffice.extra_plots_make_every * 1000

  if (
    extra_plots_dir is None or
    not (extra_plots_dir.exists() or extra_plots_dir.parent.exists())
  ):
    logging.warning(
      f'Predicu plots not generated, as extra_plots_dir '
      f'is not valid directory: {extra_plots_dir}'
    )
  else:
    logging.info(
      f"Registering periodic callback: generate_predicu_plots "
      f"/{repeat_every/1000}s"
    )
    callback = AnalyticsCallback(config.backoffice.extra_plots_dir, db_factory)
    ioloop.PeriodicCallback(callback.generate_plots, repeat_every).start()
