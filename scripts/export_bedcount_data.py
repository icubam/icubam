#!/usr/bin/env python

from absl import app
from absl import flags

from icubam.www.handlers.db import DBHandler
from icubam.db import sqlite

flags.DEFINE_string("db_path", "test.db", "Path to SQLite3 database.")
flags.DEFINE_string('out_path', '/tmp/bedcount.h5', 'Output file.')
FLAGS = flags.FLAGS

def main(argv):
  if not FLAGS.out_path.endswith(".h5"):
    raise ValueError(
      f"Expected output file to end with `.h5'. Got {FLAGS.out_path} instead"
    )
  sqldb = sqlite.SQLiteDB(FLAGS.db_path)
  data = sqldb.get_bedcount()
  data.to_hdf(FLAGS.out_path, 'data')

if __name__ == "__main__":
  app.run(main)
