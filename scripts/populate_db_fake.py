from absl import app
from absl import flags
from icubam.db import sqlite
from icubam import config

flags.DEFINE_string('config', 'resources/config.toml', 'Config file.')
flags.DEFINE_enum('mode', 'dev', ['prod', 'dev'], 'Run mode.')


def main(unused_argv):
  cfg = config.Config(FLAG.config, mode=FLAGS.mode)
  sdb = sqlite.SQLiteDB(cfg.db.sqlite_path)

  sdb.upsert_icu(
    'A. Beclere', '92', 'Clamart', 48.788055555555545, 2.2547222222222216, 'test_tel')
  sdb.upsert_icu(
    'A. Pare', '93', 'Unknown', 48.84916666666667, 2.2355555555555555, 'test_tel')
  sdb.upsert_icu(
    'Avicenne', '93', 'Bobigny', 48.914722222222224, 2.4241666666666664, 'test_tel')
  sdb.upsert_icu(
    'Beaujon', '93', 'Bobigny', 48.90833333333333, 2.310277777777777, 'test_tel')
  sdb.upsert_icu(
    'Bicetre', '93', 'Kremelin-Bicetre', 48.81, 2.353888888888889, 'test_tel')

  sdb.update_bedcount(1, 'A. Beclere', 23, 4, 12, 200, 34, 7, 1)
  sdb.update_bedcount(2, 'A. Pare', 3, 14, 12, 200, 3, 7, 1)
  sdb.update_bedcount(3, 'Avicenne', 12, 23, 12, 200, 34, 12, 1)
  sdb.update_bedcount(4, 'Beaujon', 5, 6, 12, 200, 34, 7, 1)
  sdb.update_bedcount(5, 'Bicetre', 9, 2, 12, 200, 34, 44, 1)

  sdb.add_user('Bicetre', 'user1', '+336666666', 'wtf')
  sdb.add_user('Avicenne', 'user2', '+336699999', 'wthjhf')


if __name__ == "__main__":
  app.run(main)
