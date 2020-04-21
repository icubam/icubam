import asyncio
import datetime
import logging
import os
import sys
from pathlib import Path

import click

from icubam.config import Config
from icubam.db.store import create_store_factory_for_sqlite_db
from icubam.predicu.analytics_server import AnalyticsCallback
from icubam.predicu.data import load_bedcounts


@click.group()
def cli():
  pass


@cli.command(name="export")
@click.option("--output-dir", "-o", default="/tmp", type=str)
@click.option("--api-key", default=None)
@click.option("--spread-cum-jump-correction", default=False, type=bool)
@click.option("--icubam-host", default="localhost", type=str)
@click.option(
  "--max-date",
  default=None,
  help="max date of the exported data (e.g. 2020-04-05)",
  type=str
)
def export_data(
  output_dir, api_key, spread_cum_jump_correction, icubam_host, max_date
):
  if not os.path.isdir(output_dir):
    logging.info("creating directory %s" % output_dir)
    os.makedirs(output_dir)
  logging.info("exporting data to %s" % output_dir)
  if not os.path.isdir(output_dir):
    raise IOError(f"Output dir `{output_dir}' does not exist.")
  datetimestr = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")
  filename = "predicu_data_preprocessed_{}.csv".format(datetimestr)
  path = os.path.join(output_dir, filename)
  d = load_bedcounts(
    preprocess=True,
    api_key=api_key,
    max_date=max_date,
    icubam_host=icubam_host,
    spread_cum_jump_correction=spread_cum_jump_correction,
  )
  d.to_csv(path)
  logging.info("export DONE.")


@cli.command(name="make_dashboard_plots", help="Make dasboard plots ")
@click.option(
  "--config", "-o", type=str, required=True, help="ICUBAM config file."
)
@click.option(
  "--output-dir",
  "-o",
  type=str,
  help=(
    "Output directory where to store plots. If not provided "
    "config.backoffice.extra_plots_dir is used."
  )
)
def make_dasboard_plots(config, output_dir):
  config = Config(config)
  # Make sure DB path exists, to avoid creating an empty one
  if not Path(config.db.sqlite_path).exists():
    click.echo(f"Could not find DB at {config.db.sqlite_path}!", err=True)
    sys.exit(1)

  if output_dir is None:
    output_dir = config.backoffice.extra_plots_dir

  output_dir = Path(output_dir)
  if not output_dir.exists():
    if not output_dir.parent.exists():
      click.echo(f"Output directory {output_dir}!", err=True)
      sys.exit(1)
    # otherwise necessary folder will be created by generate_plots

  store_factory = create_store_factory_for_sqlite_db(config)
  callback = AnalyticsCallback(output_dir, store_factory)
  eventloop = asyncio.new_event_loop()
  eventloop.run_until_complete(callback.generate_plots())
  click.echo(f'Generated dashboard plots in {output_dir}')


if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  cli()
