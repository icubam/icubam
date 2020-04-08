import csv
import sys
from absl import app
from absl import flags
from icubam import config
from icubam.db import sqlite

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
FLAGS = flags.FLAGS

def main(argv):
	cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
	sqldb = sqlite.SQLiteDB(cfg.db.sqlite_path)
	csv_data = csv.reader(open('ICU.csv'))

	expected_column = ['icu_name', 'region', 'dept', 'city', 'lat', 'long', 'telephone']
	header = next(csv_data, None) 

	for c in expected_column :
		if c not in header :
			print("ERROR : invalid csv file, missing column " + c + " in header")
			sys.exit(0)

	for row in csv_data:
		region_id = sqldb.upsert_region(row[header.index("region")])

		row_info = {
			"name":				row[header.index("icu_name")],
			"region_id":	region_id,
			"dept": 			row[header.index("dept")],
			"city": 			row[header.index("city")],
			"lat": 				row[header.index("lat")],
			"long":     	row[header.index("long")],
			"telephone":	row[header.index("telephone")],
		}
		print(row_info)
		sqldb.upsert_icu(**row_info)

if __name__ == "__main__":
  app.run(main)