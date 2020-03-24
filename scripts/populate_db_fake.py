from absl import app
from absl import flags
from icubam.db import sqlite

flags.DEFINE_string('db_path', 'test.db', 'File for the db.')
FLAGS = flags.FLAGS


def main(unused_argv):
  sdb = sqlite.SQLiteDB(FLAGS.db_path)

  sdb.add_icu(
    'A. Beclere', '92', 'Clamart', 48.788055555555545, 2.2547222222222216, 'test_tel')
  sdb.add_icu(
    'A. Pare', '92', 'Unknown', 48.84916666666667, 2.2355555555555555, 'test_tel')
  sdb.add_icu(
    'Avicenne', '93', 'Bobigny', 48.914722222222224, 2.4241666666666664, 'test_tel')
  sdb.add_icu(
    'Beaujon', '93', 'Bobigny', 48.90833333333333, 2.310277777777777, 'test_tel')
  sdb.add_icu(
    'Bicetre', '94', 'Kremelin-Bicetre', 48.81, 2.353888888888889, 'test_tel')

  sdb.update_bedcount(1, 'A. Beclere', 23, 4, 12, 200, 34, 7)
  sdb.update_bedcount(2, 'A. Pare', 3, 14, 12, 200, 3, 7)
  sdb.update_bedcount(3, 'Avicenne', 12, 23, 12, 200, 34, 12)
  sdb.update_bedcount(4, 'Beaujon', 5, 6, 12, 200, 34, 7)
  sdb.update_bedcount(5, 'Bicetre', 9, 2, 12, 200, 34, 44)

  sdb.add_user('Bicetre', 'user1', '+336666666', 'wtf')
  sdb.add_user('Avicenne', 'user2', '+336699999', 'wthjhf')


if __name__ == "__main__":
  app.run(main)
