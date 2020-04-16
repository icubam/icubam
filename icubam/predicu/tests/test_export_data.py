import collections

import icubam.predicu.__main__
import icubam.predicu.data
import icubam.predicu.test_utils


def make_monkeypatch_load_bedcounts(data):
  def monkeypatch_load_bedcounts(*args, **kwargs):
    return data

  return monkeypatch_load_bedcounts


def test_export_data(tmpdir, monkeypatch):
  cached_data = icubam.predicu.test_utils.load_test_data()
  monkeypatch.setattr(
    icubam.predicu.data, 'load_bedcounts',
    make_monkeypatch_load_bedcounts(cached_data['bedcounts'])
  )
  TestArgs = collections.namedtuple(
    'TestArgs', [
      'output_dir', 'api_key', 'max_date', 'icubam_host',
      'spread_cum_jump_correction'
    ]
  )
  test_args = TestArgs(
    output_dir=str(tmpdir),
    api_key='test_api_key',
    max_date=None,
    icubam_host='localhost',
    spread_cum_jump_correction=False,
  )
  icubam.predicu.__main__.export_data(test_args)
