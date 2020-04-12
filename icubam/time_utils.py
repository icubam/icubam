from typing import Tuple, Union
import functools
import time
import datetime

UNITS = [(86400, 'day'), (3600, 'hour'), (60, 'minute'), (1, 'second')]


def time_ago(ts, ts_reference=None) -> Tuple[int, str]:
  """Returns how long ago when ts compared to ts_reference.

  Args:
   ts: the timestamp (int, float or None) we want to know how long ago it was.
   ts_reference: the reference timestamp, setting the zero. If not set, we use
    the current timestamp.

  Returns:
    A tuple (count, unit), corresponding to the most significant time unit.
    For instance (3, 'hour') for 3 hours ago. (27, 'second') for 27 seconds ago.
  """
  if ts is None:
    return -1, 'never'

  ts_reference = int(
    datetime.datetime.utcnow().timestamp()
  ) if ts_reference is None else ts_reference
  delta = int(ts_reference - int(ts))
  for unit, name in sorted(UNITS, reverse=True):
    curr = delta // unit
    if curr > 0:
      return curr, name
  return curr, 'now'


def is_stale(ts, ts_reference=None, days_threshold=1) -> bool:
  if ts is None:
    return True

  if ts_reference is None:
    ts_reference = int(datetime.datetime.utcnow().timestamp())
  delta = int(ts_reference - ts)
  return delta > days_threshold * 86400


def localewise_time_ago(ts, locale, ts_reference=None):
  count, units = time_ago(ts, ts_reference)
  if count <= 0:
    return locale.translate(units) if locale else units

  template = "{delta} {units} ago"
  if locale is not None:
    units = locale.translate(units, units, count)
    template = locale.translate(template)
  return template.format(delta=count, units=units)


def parse_hour(hour, sep=':') -> Tuple:
  """Returns a tuple of integer from an hour like '14:34'."""
  if not isinstance(hour, str):
    return hour
  try:
    return tuple([int(x) for x in hour.split(sep)])
  except Exception as e:
    return "", ""


def get_next_timestamp(hours, ts=None):
  """Gets the timestamp of the next hour in the list based on ts (or now).

  Args:
   hours: a list of tuples (hour, minute)
   ts: an optional timestamp. If none, use the current timestamp.
  """
  if not hours:
    return None

  ts = int(time.time()) if ts is None else ts
  now = datetime.datetime.fromtimestamp(ts)
  today_fn = functools.partial(
    datetime.datetime, year=now.year, month=now.month, day=now.day
  )
  next = None
  sorted_moments = sorted(hours)
  for hm in sorted_moments:
    curr = today_fn(hour=hm[0], minute=hm[1])
    if curr > now:
      next = curr
      break
  if next is None:
    hm = sorted_moments[0]
    next = today_fn(hour=hm[0], minute=hm[1]) + datetime.timedelta(1)
  return next.timestamp()
