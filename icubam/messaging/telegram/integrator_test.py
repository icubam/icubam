from unittest import mock
import tornado.queues
import tornado.testing

from icubam import config
from icubam.db import store
from icubam.messaging.telegram import integrator, mock_bot


class TelegramSetupTest(tornado.testing.AsyncTestCase):
  """Tests for the integrator class."""
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    tg_bot = mock_bot.MockTelegramBot(self.config)
    factory = store.create_store_factory_for_sqlite_db(self.config)
    self.db = factory.create()
    self.queue = tornado.queues.Queue()
    self.integrator = integrator.TelegramSetup(
      self.config, self.db, scheduler=None, tg_bot=tg_bot
    )

  def test_uses_webhook(self):
    self.assertFalse(self.integrator.uses_webhook)
    self.config.server.base_url = 'https://www.example.com/'
    self.assertTrue(self.integrator.uses_webhook)

  def test_ison(self):
    self.assertTrue(self.integrator.is_on)
    self.config.TELEGRAM_API_KEY = None
    self.assertFalse(self.integrator.is_on)

  def test_setup_fetching(self):
    callbacks = []
    self.integrator._start_periodic_fetching = mock.MagicMock(
      return_value=None
    )
    self.integrator.setup_fetching(callbacks)
    self.assertEqual(len(callbacks), 1)

    # This should set up the webhook.
    self.config.server.base_url = 'https://www.example.com/'
    callbacks = []
    self.integrator.setup_fetching(callbacks)
    self.assertEqual(len(callbacks), 2)

  def test_add_routes(self):
    app_routes = []
    self.integrator.add_routes(app_routes)
    self.assertEqual(len(app_routes), 0)

    self.config.server.base_url = 'https://www.example.com/'
    self.integrator.add_routes(app_routes)
    self.assertGreater(len(app_routes), 0)
