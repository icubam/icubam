from absl.testing import absltest
import os
from icubam.www.handlers.upload_csv import clean_path


class TokenTest(absltest.TestCase):
  def test_sanitize(self):
    root_path = ['', '/foo/bar', '/foo/bar/']
    file_path = {
      '../../././././blah.___csv___': 'blah.___csv___',
      "{ '\ : []]{$ROOT": 'root'
    }
    for rp in root_path:
      for fp in file_path:
        test_path = os.path.join(rp, fp)
        c_path = clean_path(test_path)
        good_name = file_path[fp]
        self.assertEqual(good_name, c_path)
