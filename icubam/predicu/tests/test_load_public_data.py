import datetime

import pytest

from ..data import load_public


@pytest.mark.slow
def test_load_public_data():
  data = load_public()
  max_date = data.date.max()
  now = datetime.datetime.now()
  if now.hour < 20:
    expected_date = (now - datetime.timedelta(days=1)).date()
  else:
    expected_date = now.date()
  assert max_date == expected_date
