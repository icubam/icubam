"""Generates plots using icubam.analytic"""
import asyncio
import logging
import sys
from pathlib import Path

from absl import app, flags

from icubam import config
from icubam.analytics.analytics_server import AnalyticsCallback
from icubam.db.store import create_store_factory_for_sqlite_db

flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string('output_dir', '/tmp', 'Output dir for plots.')
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config)
  output_dir = FLAGS.output_dir

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
    # otherwise necessary folder will be created by generate_plots

  store_factory = create_store_factory_for_sqlite_db(cfg)
  callback = AnalyticsCallback(output_dir, store_factory)
  eventloop = asyncio.new_event_loop()
  eventloop.run_until_complete(callback.generate_plots())
  print(f'Generated dashboard plots in {output_dir}')


if __name__ == '__main__':
  app.run(main)
