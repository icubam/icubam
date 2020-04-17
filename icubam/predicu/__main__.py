import argparse
import datetime
import logging
import os

from icubam.predicu.data import load_bedcounts


def export_data(args):
  output_dir = args.output_dir
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
    api_key=args.api_key,
    max_date=args.max_date,
    icubam_host=args.icubam_host,
    spread_cum_jump_correction=args.spread_cum_jump_correction,
  )
  d.to_csv(path)
  logging.info("export DONE.")


if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()
  parser_export = subparsers.add_parser("export", help="export data")
  parser_export.set_defaults(func=export_data)
  parser_export.add_argument("--output-dir", "-o", default="/tmp/")
  parser_export.add_argument("--api-key", default=None)
  parser_export.add_argument(
    "--spread-cum-jump-correction", default=False, action="store_true"
  )
  parser_export.add_argument("--icubam-host", default="localhost")
  parser_export.add_argument(
    "--max-date",
    default=None,
    help="max date of the exported data (e.g. 2020-04-05)",
  )
  args = parser.parse_args()
  args.func(args)
