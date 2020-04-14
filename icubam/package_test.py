import icubam


def test_version():
  try:
    icubam.__version__
  except Exception:
    raise AssertionError
