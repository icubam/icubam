import csv
import sys
from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db.store import Store, StoreFactory, BedCount, ExternalClient, ICU, Region, User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import DetachedInstanceError

flags.DEFINE_string("config", "resources/config.toml", "Config file.")
flags.DEFINE_string("dotenv_path", "resources/.env", "Config file.")
flags.DEFINE_enum("mode", "dev", ["prod", "dev"], "Run mode.")
FLAGS = flags.FLAGS

def main(argv):
	# argv[1] : path to csv file
	cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
	store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
	store = store_factory.create()

	csv_path = sys.argv[1]
	csv_data = csv.reader(open(csv_path))

	# create default admin
	admin_user_id = store.add_default_admin()

	# check header
	header = next(csv_data, None) 
	expected_column = ['icu_name', 'region', 'dept', 'city', 'lat', 'long', 'telephone']
	for c in expected_column :
		if c not in header :
			print("ERROR : invalid csv file, missing column " + c + " in header")
			sys.exit(0)

	for row in csv_data:
		# insert ICU region if needed
		region = store.get_region_by_name(row[header.index("region")])
		if region:
			region_id = region.region_id 
		else :
			region_id = store.add_region(admin_user_id, Region(name=row[header.index("region")]))

		# insert ICU if needed
		icu = store.get_icu_by_name(row[header.index("icu_name")])
		if icu:
			print("IMPORT CSV : ICU " + row[header.index("icu_name")] + " already exist in db")
		else:
			# create ICU
			icu_info = {
				"name":				row[header.index("icu_name")],
				"region_id":	region_id,
				"dept": 			row[header.index("dept")],
				"city": 			row[header.index("city")],
				"lat": 				row[header.index("lat")],
				"long":     	row[header.index("long")],
				"telephone":	row[header.index("telephone")],
			}
			icu_id = store.add_icu(admin_user_id, ICU(**icu_info))
			
			# create ICU default user
			user_info = {
				"name":				row[header.index("icu_name")] + "_user",
				"telephone":	row[header.index("telephone")],
				"email":			"a@bc.org",
				"is_active":	True,
				"is_admin":		False,
			}
			user_id = store.add_user_to_icu(admin_user_id ,icu_id, User(**user_info))

			# update bed_count
			bed_info = {
				"icu_id": icu_id,
				"n_covid_occ": 0,
				"n_covid_free": 0,
				"n_ncovid_occ": 0,
				"n_ncovid_free": 0,
				"n_covid_deaths": 0,
				"n_covid_healed": 0,
				"n_covid_refused": 0,
				"n_covid_transfered": 0,
			}
			store.update_bed_count_for_icu(user_id, BedCount(**bed_info))

if __name__ == "__main__":
  app.run(main)