import pathlib
from absl import logging  # noqa: F401

from icubam.analytics import plots


class PlotGenerator:
  """Generates all the plots periodically."""

  DEFAULT = ['barplot_beds_per', 'barplot_flow_per']

  def __init__(self, config, db, dataset, frequency=None):
    self.config = config
    self.db = db

    self.folder = config.backoffice.extra_plots_dir
    if not isinstance(self.folder, str):
      self.folder = None
    else:
      extra_plots_dir = pathlib.Path(self.folder)
      if not (extra_plots_dir.exists() or extra_plots_dir.parent.exists()):
        self.folder = None

    self.dataset = dataset
    self.frequency = None
    if frequency is not None and frequency > 0:
      self.frequency = frequency

  @property
  def is_valid(self):
    return self.frequency is not None and self.folder is not None

  async def run(self, names=None):
    df = self.dataset.get_bedcounts(latest=False)
    logging.info('[periodic callback] Starting plots generation with predicu')
    plots.generate_plots(
      plots=self.DEFAULT if names is None else names,
      data={'bedcounts': df},
      output_dir=self.folder
    )
    logging.info(f'plots generated in {self.folder}')

  def register(self, ioloop) -> None:
    """Register a callback to generate plots"""
    if not self.is_valid:
      logging.warning("PlotGenerator is not properly configured.")
      return

    repeat_every = self.frequency * 1000
    logging.info(
      f"Registering periodic callback: generate_predicu_plots /{self.frequency}s"
    )
    ioloop.PeriodicCallback(self.run, repeat_every).start()
