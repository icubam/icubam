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

flags.DEFINE_bool("forceUpdate", False, "replace db content with csv if entry already exist.")
flags.DEFINE_string("icu_csv_path", "resources/icu.csv", "path to csv file containing ICU data")
flags.DEFINE_string("user_csv_path", "resources/user.csv", "path to csv file containing user data")

FLAGS = flags.FLAGS


def main(args=None):
	csv = CSV()
	admin_user_id = csv.get_default_admin()
	csv.import_icus(admin_user_id, FLAGS.icu_csv_path, FLAGS.forceUpdate)
	csv.import_users(admin_user_id, FLAGS.user_csv_path, FLAGS.forceUpdate)

class CSV:
	""" """

	def __init__(self):
		cfg = config.Config(FLAGS.config, mode=FLAGS.mode, env_path=FLAGS.dotenv_path)
		store_factory = db_store.create_store_factory_for_sqlite_db(cfg)
		self.store = store_factory.create()

	def get_default_admin(self):
		# create default admin
		return self.store.add_default_admin()

	def import_icus(self,admin_user_id: int, csv_file_path:str, forceUpdate=False):
		csv_data = csv.reader(open(csv_file_path))

		# check header
		header = next(csv_data, None) 
		expected_column = ['icu_name', 'region', 'dept', 'city', 'lat', 'long', 'telephone']
		for c in expected_column :
			if c not in header :
				print("IMPORT CSV : ERROR : invalid ICU file, missing column " + c + " in header")
				sys.exit(0)

		for row in csv_data:
			# insert ICU region if needed
			region = self.store.get_region_by_name(row[header.index("region")])
			if region:
				region_id = region.region_id 
			else :
				region_id = self.store.add_region(admin_user_id, Region(name=row[header.index("region")]))

			# insert ICU if needed
			icu = self.store.get_icu_by_name(row[header.index("icu_name")])
			icu_info = {
				"name":				row[header.index("icu_name")],
				"region_id":	region_id,
				"dept": 			row[header.index("dept")],
				"city": 			row[header.index("city")],
				"lat": 				row[header.index("lat")],
				"long":     	row[header.index("long")],
				"telephone":	row[header.index("telephone")],
			}
			if icu:
				# update ICU
				if forceUpdate:
					icu_id = icu.icu_id
					self.store.update_icu(admin_user_id, icu_id, icu_info)
					print("IMPORT CSV : overwrite ICU " + row[header.index("icu_name")] + " --forceUpdate")
				else:
					print("IMPORT CSV : skip ICU " + row[header.index("icu_name")] + " already exist in db (use --forceUpdate to update anyway)")
			else:
				# create ICU
				icu_id = self.store.add_icu(admin_user_id, ICU(**icu_info))
				print("IMPORT CSV : create ICU " + row[header.index("icu_name")])
				'''
				# create ICU default user
				user_info = {
					"name":				row[header.index("icu_name")] + "_user",
					"telephone":	row[header.index("telephone")],
					"email":			"a@bc.org",
					"is_active":	True,
					"is_admin":		False,
				}
				user_id = self.store.add_user_to_icu(admin_user_id ,icu_id, User(**user_info))

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
				self.store.update_bed_count_for_icu(user_id, BedCount(**bed_info))
				'''

	def import_users(self,admin_user_id: int, csv_file_path:str, forceUpdate=False):
		csv_data = csv.reader(open(csv_file_path))

		# check header
		header = next(csv_data, None) 
		expected_column = ['icu_name', 'name', 'tel', 'description']
		for c in expected_column :
			if c not in header :
				print("IMPORT CSV : ERROR : invalid USER file, missing column " + c + " in header")
				sys.exit(0)

		for row in csv_data:
			user = self.store.get_user_by_phone(row[header.index("tel")])
			user_info = {
				"name":				row[header.index("name")],
				"telephone":	row[header.index("tel")],
				"description":row[header.index("description")],
				"email":			"a@bc.org",
				"is_active":	True,
				"is_admin":		False,
			}

			if user:
				# update USER
				if forceUpdate:
					self.store.update_user(admin_user_id, user.user_id, user_info)
					print("IMPORT CSV : overwrite USER " + row[header.index("name")] + " --forceUpdate")
				else:
					print("IMPORT CSV : skip USER " + row[header.index("name")] + " already exist in db (use --forceUpdate to update anyway)")
			else:
				# create USER
				icu = self.store.get_icu_by_name(row[header.index("icu_name")])
				if icu:
					self.store.add_user_to_icu(admin_user_id ,icu.icu_id, User(**user_info))
					print("IMPORT CSV : create ICU " + row[header.index("name")])
				else:
					print("IMPORT CSV : skip USER " + row[header.index("name")] + ", no existing ICU named " + row[header.index("icu_name")] +
								". you should import/create this ICU first")

		
if __name__ == "__main__":
	app.run(main)