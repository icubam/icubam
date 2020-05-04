from icubam.analytics import generator, dataset
from icubam.config import Config


class MockIOLoop:
  n_calls = 0

  def PeriodicCallback(self, func, repeat_every):
    self.n_calls += 1

    class MockCallback():
      def start(self):
        ...

    return MockCallback()


def test_generator(tmpdir):
  config = Config('resources/test.toml')
  ds = dataset.Dataset(None)

  # Non existing path, callback not registred
  for _l in ['/invalid/path/2', None]:
    config.backoffice.extra_plots_dir = '/invalid/path/2'
    gen = generator.PlotGenerator(config, None, ds, frequency=100)
    ioloop = MockIOLoop()
    gen.register(ioloop)
    assert ioloop.n_calls == 0

  # Callback registered
  config.backoffice.extra_plots_dir = str(tmpdir.mkdir("tmp"))
  gen = generator.PlotGenerator(config, None, ds, frequency=100)
  ioloop = MockIOLoop()
  gen.register(ioloop)
  assert ioloop.n_calls == 1

  # Negative frequency: do not register.
  gen = generator.PlotGenerator(config, None, ds, frequency=-1)
  ioloop = MockIOLoop()
  gen.register(ioloop)
  assert ioloop.n_calls == 0
