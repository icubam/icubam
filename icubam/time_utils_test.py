import datetime

from icubam import time_utils


def test_time_ago():
  ref = datetime.datetime(2020, 3, 27, 16, 30).timestamp()
  ts = datetime.datetime(2020, 3, 27, 16, 0).timestamp()
  assert time_utils.time_ago(ts, ref) == (30, 'minute')

  ts = datetime.datetime(2020, 3, 24, 16, 0).timestamp()
  assert time_utils.time_ago(ts, ref) == (3, 'day')

  ts = datetime.datetime(2020, 3, 26, 17, 0).timestamp()
  assert time_utils.time_ago(ts, ref) == (23, 'hour')

def test_parse_hour_test():
  assert time_utils.parse_hour("23:12") == (23, 12)
  assert time_utils.parse_hour("23h12", sep='h') == (23, 12)
  assert time_utils.parse_hour("wqw") == ("", "")
  assert time_utils.parse_hour(23.12) == (23.12)

def test_localewise_time_ago():
  ref = datetime.datetime(2020, 3, 27, 16, 30).timestamp()
  assert time_utils.localewise_time_ago(None, None, ref) == 'never'
  ts = datetime.datetime(2020, 3, 27, 16, 30).timestamp()
  assert time_utils.localewise_time_ago(ts, None, ref) == 'now'
  ts = datetime.datetime(2020, 3, 27, 16, 25).timestamp()
  assert time_utils.localewise_time_ago(ts, None, ref) == '5 minute ago'

def test_get_next_timestamp():
  pings = [(12, 8), (14, 51)]
  ts = datetime.datetime(2020, 3, 26, 4, 0).timestamp()
  next_one = time_utils.get_next_timestamp(pings, ts)
  expected_next = datetime.datetime(2020, 3, 26, 12, 8).timestamp()
  assert next_one == expected_next

  ts = datetime.datetime(2020, 3, 26, 12, 10).timestamp()
  next_one = time_utils.get_next_timestamp(pings, ts)
  expected_next = datetime.datetime(2020, 3, 26, 14, 51).timestamp()
  assert next_one == expected_next

  ts = datetime.datetime(2020, 3, 26, 18, 10).timestamp()
  next_one = time_utils.get_next_timestamp(pings, ts)
  expected_next = datetime.datetime(2020, 3, 27, 12, 8).timestamp()
  assert next_one == expected_next

  next_one = time_utils.get_next_timestamp(None, ts)
  assert next_one == None

def test_is_stale():
  ts = datetime.datetime(2020, 3, 27, 16, 30).timestamp()
  ref = datetime.datetime(2020, 3, 28, 17, 30).timestamp()
  assert time_utils.is_stale(ts, ref, days_threshold=1) == True
  assert time_utils.is_stale(ts, ref, days_threshold=2) == False
