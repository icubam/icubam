import asyncio
import logging
import sys
from pathlib import Path

import click

from icubam.config import Config
from icubam.db.store import create_store_factory_for_sqlite_db
from icubam.analytics.analytics_server import AnalyticsCallback
from icubam.analytics.plot import generate_plots


@click.group()
def cli():
  pass


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
def make_dashboard_plots(config, output_dir):
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


@cli.command(
  name="plot",
  help="Specific plots to generate (all are by default).",
)
@click.option(
  "--output-dir",
  "-o",
  default="/tmp",
  type=str,
  help="Directory where the resulting plots will be stored."
)
@click.argument(
  "plots",
  nargs=-1,
)
def plot_cli(**kwargs):
  import matplotlib
  matplotlib.use("Agg")
  if not kwargs['plots']:
    kwargs['plots'] = None
  generate_plots(**kwargs)


if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  cli()
