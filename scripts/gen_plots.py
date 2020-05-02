"""Generates plots using icubam.analytic"""
import asyncio
import logging
import sys
from pathlib import Path

from absl import app, flags

from icubam import config
from icubam.analytics import dataset, plots, preprocessing
from icubam.analytics.analytics_server import AnalyticsCallback
from icubam.db.store import create_store_factory_for_sqlite_db

flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string('output_dir', '/tmp', 'Output dir for plots.')
flags.DEFINE_string('plot_name', 'dashboard_default', 'Plot name.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config)
  output_dir = FLAGS.output_dir
  plot_name = FLAGS.plot_name

  # Make sure DB path exists, to avoid creating an empty one
  if not Path(cfg.db.sqlite_path).exists():
    logging.error(f"Could not find DB at {cfg.db.sqlite_path}")
    sys.exit(1)

  if output_dir is None:
    output_dir = cfg.backoffice.extra_plots_dir

  output_dir = Path(output_dir)
  if not output_dir.exists():
    if not output_dir.parent.exists():
      logging.error(f"Output directory {output_dir} does not exist.")
      sys.exit(1)

  store_factory = create_store_factory_for_sqlite_db(cfg)
  if plot_name == 'dashboard_default':
    callback = AnalyticsCallback(output_dir, store_factory)
    eventloop = asyncio.new_event_loop()
    eventloop.run_until_complete(callback.generate_plots())
    logging.info(f'Generated dashboard plots in {output_dir}')
  else:
    df_bedcounts = dataset.load_bed_counts(store_factory.create())
    df_bedcounts = preprocessing.preprocess_bedcounts(df_bedcounts)
    logging.info('[periodic callback] Starting plots generation with predicu')
    plot_data = {'bedcounts': df_bedcounts}
    plots.generate_plots([plot_name], plot_data, output_dir=output_dir)
    print(f'Generated dashboard plots in {output_dir}')


if __name__ == '__main__':
  app.run(main)
