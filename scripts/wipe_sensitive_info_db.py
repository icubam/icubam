"""
Wipes sensitive information from an ICUBAM DB.
Warning: modifies data in-place!
"""

from absl import app
from absl import flags
import click
import sqlite3
import sys

flags.DEFINE_boolean("quiet", False, "Do not prompt user confirmation")
flags.DEFINE_boolean(
  "keep_beds", False, "Whether to keep bed occupation data."
)
FLAGS = flags.FLAGS

ALTERATIONS = {
  "bed_counts": [
    ("n_ncovid_free", 3),
    ("n_ncovid_occ", 5),
    ("n_covid_deaths", 0),
    ("n_covid_healed", 0),
    ("n_covid_refused", 0),
    ("n_covid_transfered", 0),
    ("message", '"Have a nice day!"'),
  ],
  "icus": [("telephone", "33120000000 + icus.icu_id")
           ],  # we reuse the ID to respect telephone uniqueness constraint
  "users": [
    ("name", '"Jean Dumont"'),
    ("email", '"jean.dumont@example.org"'),
    ("telephone", "33600000001 + users.user_id"),
    ("password_hash", 42),
  ],
  "external_clients": [
    ("name", '"Jean Dumont"'),
    ("email", '"jean.dumont@example.org"'),
    ("telephone", "33600000001 + external_clients.external_client_id"),
  ],
}


def wipe_db(path):
  conn = sqlite3.connect(path)
  cur = conn.cursor()
  if not FLAGS.keep_beds:
    ALTERATIONS["bed_counts"].extend([("n_covid_free", 2), ("n_covid_occ", 4)])
  for alteration in ALTERATIONS.items():
    affectations = ",".join([f"{k} = {v}" for (k, v) in alteration[1]])
    query = f"UPDATE {alteration[0]} SET {affectations};"
    if not FLAGS.quiet:
        print(query)
    conn.execute(query)
  conn.commit()
  conn.close()


def main(argv):
  if len(argv) < 2:
    print(f"Usage: {argv[0]} DB_PATH")
    sys.exit(-1)

  if not FLAGS.quiet:
    if not click.confirm(
      "WARNING: THIS WILL WIPE THE DATABASE IN-PLACE. CONTINUE?", err=True
    ):
      sys.exit(0)

  wipe_db(argv[1])


if __name__ == "__main__":
  app.run(main)
