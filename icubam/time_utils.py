from typing import Optional, Tuple, Union
import time
import datetime

UNITS = [
  (86400, 'day'),
  (3600, 'hour'),
  (60, 'minute'),
  (1, 'second')
]


def time_ago(ts: Optional[Union[int, float]]) -> Tuple[int, str]:
  """Returns the timedelta and its unit between now and the timestamp."""
  if ts is None:
    return -1, 'never'

  delta = int(time.time() - int(ts))

  for unit, name in sorted(UNITS, reverse=True):
    curr = delta // unit
    if curr > 0:
      return curr, name
  return curr, 'now'


def localwise_time_ago(ts, locale):
  count, unit = time_ago(ts)
  local_units = locale.translate(unit, unit, count)
  return locale.translate("{delta} {units} ago").format(
    delta=count, units=local_units)


def parse_hour(hour, sep=':') -> tuple:
  """Returns a tuple of integer from an hour like '14:34'."""
  if not isinstance(hour, str):
    return hour
  return tuple([int(x) for x in hour.split(sep)])


def get_next_timestamp(pings, ts=None):
  """Gets the timestamp of the next ping in the list based on ts (or now).

  Args:
   pings: a list of tuples (hour, minute)
   ts: an optional timestamp. If none, use the current timestamp.
  """
  if not pings:
    return None

  ts = int(time.time()) if ts is None else ts
  now = datetime.datetime.fromtimestamp(ts)
  today_fn = functools.partial(
    datetime.datetime, year=now.year, month=now.month, day=now.day)
  next = None
  sorted_moments = sorted(self.when)
  for hm in sorted_moments:
    curr = today_fn(hour=hm[0], minute=hm[1])
    if curr > now:
      next = curr
      break
  if next is None:
    hm = sorted_moments[0]
    next = today_fn(hour=hm[0], minute=hm[1]) + datetime.timedelta(1)
  return next.timestamp()
