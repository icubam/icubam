"""Generates plots using icubam.analytics."""

import asyncio
import logging
from pathlib import Path

from absl import app, flags

from icubam import config
from icubam.analytics import dataset, generator
from icubam.db import store

flags.DEFINE_string('config', config.DEFAULT_CONFIG_PATH, 'Config file.')
flags.DEFINE_string(
  'plot_name', None, 'Plot name. If None, generate default plots.'
)
flags.DEFINE_string(
  'output_dir', None,
  'Where to write the images. If not use the one in config.'
)
FLAGS = flags.FLAGS


def main(argv):
  cfg = config.Config(FLAGS.config)

  # Make sure DB path exists, to avoid creating an empty one
  if not Path(cfg.db.sqlite_path).exists():
    logging.error(f"Could not find DB at {cfg.db.sqlite_path}")
    return

  if FLAGS.output_dir is not None:
    cfg.analytics.extra_plots_dir = FLAGS.output_dir

  db = store.create_store_factory_for_sqlite_db(cfg).create()
  plot_generator = generator.PlotGenerator(cfg, db, dataset.Dataset(db))
  eventloop = asyncio.new_event_loop()
  eventloop.run_until_complete(plot_generator.run([FLAGS.plot_name]))


if __name__ == '__main__':
  app.run(main)
