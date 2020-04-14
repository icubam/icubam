import os
from icubam.www.handlers.upload_csv import clean_path


def test_sanitize():
  root_path = ['', '/foo/bar', '/foo/bar/']
  file_path = {
    r'../../././././blah.___csv___': 'blah.___csv___',
    r"{ '\ : []]{$ROOT": 'root',
    r"\\ \$BLAH.foo": 'blah.foo',
    r": () {: |: &} ;:": '',
    r"/blah/": 'blah',
    r"\/o./ /blah ../.././\$$..": ''
  }
  for rp in root_path:
    for fp in file_path:
      test_path = os.path.join(rp, fp)
      c_path = clean_path(test_path)
      good_name = file_path[fp]
      assert good_name == c_path
