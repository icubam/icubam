import pytest

from icubam.analytics.image_url_mapper import ImageURLMapper


def test_query2path():
  m = ImageURLMapper()
  assert m.make_path('some') == 'National-some.png'
  assert m.make_path('some', extension=None) == 'National-some'
  assert m.make_path('some', extension='.png') == 'National-some.png'
  assert m.make_path('some', extension='.tar.gz') == 'National-some.tar.gz'

  with pytest.raises(ValueError, match="region must be provided"):
    m.make_path('some', region_id=1)

  assert m.make_path(
    'some', region_id=1, region='A'
  ) == 'region_id=1-A-some.png'
