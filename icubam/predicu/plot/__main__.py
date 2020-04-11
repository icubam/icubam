import argparse
import logging

import matplotlib

from ..plot import DEFAULTS, generate_plots

if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  matplotlib.use("Agg")
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--api-key",
    help="API key for pulling data from ICUBAM.",
    default=DEFAULTS["api_key"],
  )
  parser.add_argument(
    "--matplotlib-style",
    help="matplotlib style used in generated plots.",
    default=DEFAULTS["matplotlib_style"],
  )
  parser.add_argument(
    "--output-dir",
    help="Directory where the resulting plots will be stored.",
    default=DEFAULTS["output_dir"],
  )
  parser.add_argument(
    "--plots",
    nargs="*",
    help="Specific plots to generate (all are by default).",
    default=DEFAULTS["plots"],
  )
  parser.add_argument(
    "--output-type",
    choices=["tex", "png", "pdf"],
    default=DEFAULTS["output_type"],
  )
  args = parser.parse_args()
  generate_plots(**args.__dict__)
