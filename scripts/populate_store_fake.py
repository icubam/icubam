"""Populates store with fake data."""
from absl import app
from absl import flags
from icubam import config
import icubam.db.store as db_store
from icubam.db.store import BedCount, ICU, Region, Store, User

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')
FLAGS = flags.FLAGS


def main(unused_argv):
  cfg = config.Config(FLAGS.config, mode=FLAGS.mode)
  store = db_store.create_store_for_sqlite_db(cfg.db.sqlite_path)

  admin_user_id = store.add_user(
      User(
          name='admin',
          telephone='+33111111111',
          email='admin@test.org',
          is_admin=True,
          password_hash=store.get_password_hash('password')))

  manager_user_id = store.add_user(
      User(
          name='manager',
          telephone='+33222222222',
          email='manager@test.org',
          password_hash=store.get_password_hash('manager')))

  region_id = store.add_region(admin_user_id, Region(name='Paris'))

  def add_icu(name, dept, city, lat, long, telephone, n_covid_occ, n_covid_free,
              n_ncovid_free, n_covid_deaths, n_covid_healed, n_covid_refused,
              n_covid_transfered):
    icu_id = store.add_icu(
        admin_user_id,
        ICU(name=name,
            region_id=region_id,
            dept=dept,
            city=city,
            lat=lat,
            long=long,
            telephone=telephone))
    store.update_bed_count_for_icu(
        admin_user_id,
        BedCount(
            icu_id=icu_id,
            n_covid_occ=n_covid_occ,
            n_covid_free=n_covid_free,
            n_ncovid_free=n_ncovid_free,
            n_covid_deaths=n_covid_deaths,
            n_covid_healed=n_covid_healed,
            n_covid_refused=n_covid_refused,
            n_covid_transfered=n_covid_transfered))
    return icu_id

  add_icu('A. Beclere', '92', 'Clamart', 48.788055555555545, 2.2547222222222216,
          'test_tel', 23, 4, 12, 200, 34, 7, 1)
  add_icu('A. Pare', '93', 'Unknown', 48.84916666666667, 2.2355555555555555,
          'test_tel', 3, 14, 12, 200, 3, 7, 1)

  icu_id = add_icu('Avicenne', '93', 'Bobigny', 48.914722222222224,
                   2.4241666666666664, 'test_tel', 12, 23, 12, 200, 34, 12, 1)
  store.add_user_to_icu(
      admin_user_id, icu_id,
      User(name='user2', telephone='+336699999', description='desc2'))
  store.assign_user_as_icu_manager(admin_user_id, manager_user_id, icu_id)

  add_icu('Beaujon', '93', 'Bobigny', 48.90833333333333, 2.310277777777777,
          'test_tel', 5, 6, 12, 200, 34, 7, 1)
  icu_id = add_icu('Bicetre', '93', 'Kremelin-Bicetre', 48.81,
                   2.353888888888889, 'test_tel', 9, 2, 12, 200, 34, 44, 1)
  store.add_user_to_icu(
      admin_user_id, icu_id,
      User(name='user1', telephone='+336666666', description='desc1'))


if __name__ == '__main__':
  app.run(main)
