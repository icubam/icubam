from icubam.predicu.analytics_server import register_analytics_callback
from icubam.config import Config


class MockIOLoop:
  n_calls = 0

  def PeriodicCallback(self, func, repeat_every):
    self.n_calls += 1

    class MockCallback():
      def start(self):
        ...

    return MockCallback()


def test_analytics_server(tmpdir):
  config = Config('resources/test.toml')

  # Non existing path, callback not registred
  for val in ['/invalid/path/2', None]:
    config.backoffice.extra_plots_dir = '/invalid/path/2'
    ioloop = MockIOLoop()
    register_analytics_callback(config, db_factory=None, ioloop=MockIOLoop())
    assert ioloop.n_calls == 0

  # Callback registered
  config.backoffice.extra_plots_dir = str(tmpdir.mkdir("tmp"))
  ioloop = MockIOLoop()
  register_analytics_callback(config, db_factory=None, ioloop=ioloop)
  assert ioloop.n_calls == 1

  # extra_plots_make_every = -1, callback not registred
  config.backoffice.extra_plots_make_every = -1
  ioloop = MockIOLoop()
  register_analytics_callback(config, db_factory=None, ioloop=MockIOLoop())
  assert ioloop.n_calls == 0
