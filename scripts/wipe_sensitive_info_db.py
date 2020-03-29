"""
Wipes sensitive information from an ICUBAM DB.
Warning: modifies data in-place!
"""

from absl import app
from absl import flags
import click
import sqlite3
import sys

flags.DEFINE_boolean('quiet', False, 'Do not prompt user confirmation')

FLAGS = flags.FLAGS

ALTERATIONS = {
    "bed_updates": [
        ("n_covid_deaths", 0),
        ("n_covid_healed", 0),
        ("n_covid_refused", 0),
        ("n_covid_transfered", 0),
        ("message", '"Have a nice day!"'),
    ],
    "icus": [("telephone", "icus.icu_id")], # we reuse the ID to respect telephone uniqueness constraint
    "users": [("name", '"Jean Dumont"'), ("telephone", "users.user_id")],
}


def wipe_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    for alteration in ALTERATIONS.items():
        affectations = ",".join([f"{k} = {v}" for (k, v) in alteration[1]])
        query = f"UPDATE {alteration[0]} SET {affectations};"
        print(query)
        conn.execute(query)
    conn.commit()
    conn.close()


def main(argv):
    if len(argv) < 2:
        print(f"Usage: {argv[0]} DB_PATH")
        sys.exit(-1)

    if not FLAGS.quiet:
        if not click.confirm("WARNING: THIS WILL WIPE THE DATABASE IN-PLACE. CONTINUE?", err=True):
            sys.exit(0)

    wipe_db(argv[1])


if __name__ == "__main__":
    app.run(main)
