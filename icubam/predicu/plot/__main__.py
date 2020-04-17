import argparse
import logging

import matplotlib

from icubam.predicu.plot import generate_plots

if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  matplotlib.use("Agg")
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--api-key",
    help="API key for pulling data from icubam.predicu.UBAM.",
    default=None,
  )
  parser.add_argument(
    "--icubam-host",
    help=
    "Host of the ICUBAM instance from icubam.predicu.ich the data should be pulled.",
    default=None,
  )
  parser.add_argument(
    "--matplotlib-style",
    help="matplotlib style used in generated plots.",
    default="seaborn-whitegrid",
  )
  parser.add_argument(
    "--output-dir",
    help="Directory where the resulting plots will be stored.",
    default="/tmp",
  )
  parser.add_argument(
    "--plots",
    nargs="*",
    help="Specific plots to generate (all are by default).",
    default=None,
  )
  parser.add_argument(
    "--output-type",
    choices=["tex", "png", "pdf"],
    default="png",
  )
  parser.add_argument(
    "--restrict-to-grand-est-region",
    action="store_true",
    help="Whether to restrict the data to the Grand-Est region data."
  )
  args = parser.parse_args()
  generate_plots(**args.__dict__)
