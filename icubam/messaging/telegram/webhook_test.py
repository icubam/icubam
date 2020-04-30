import json
import tornado.testing
from unittest import mock

from icubam import config
from icubam.db import store
from icubam.messaging import server
from icubam.messaging.telegram import integrator, mock_bot, webhook


class TelegramWebookTest(tornado.testing.AsyncHTTPTestCase):
  TEST_CONFIG = 'resources/test.toml'
  UPDATES_FILE = 'resources/test/telegram_updates.json'
  # This will make the integrator set up a webhook
  BASE_URL = 'https://www.example.com/'
  TELEGRAM_HOST = "149.154.160.0"

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG)
    self.config.server.base_url = self.BASE_URL
    tg_bot = mock_bot.MockTelegramBot(self.config)
    self.db = store.create_store_factory_for_sqlite_db(self.config).create()
    self.tg_setup = integrator.TelegramSetup(
      self.config, self.db, scheduler=None, tg_bot=tg_bot
    )
    self.tg_setup._start_periodic_fetching = mock.MagicMock(return_value=None)
    with open(self.UPDATES_FILE, 'r') as fp:
      self.update = json.load(fp)['result'][0]
    super().setUp()

  def get_app(self):
    self.server = server.MessageServer(
      self.config, port=8889, telegram_setup=self.tg_setup
    )
    return self.server.make_app()

  def post(self, host: str):
    return self.fetch(
      webhook.TelegramWebhook.ROUTE,
      method='POST',
      body=json.dumps(self.update),
      headers={"Host": host},
    )

  def test_webhook(self):
    response = self.post(self.TELEGRAM_HOST)
    self.assertEqual(response.code, 200)
    self.assertFalse(self.tg_setup.queue.empty())

  def test_webhook_from_wrong_host(self):
    response = self.post("89.145.160.0")
    self.assertEqual(response.code, 404)


class NoTelegramWebookTest(TelegramWebookTest):
  """In this test case, we test that in non https mode, there is no answer
  from the webhook endpoint. """

  # This will make the integrator not set a webhook
  BASE_URL = 'http://localhost:8787/'

  def test_webhook(self):
    response = self.post(self.TELEGRAM_HOST)
    self.assertEqual(response.code, 404)