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

  def setUp(self):
    self.config = config.Config(self.TEST_CONFIG)
    self.config.server.base_url = 'https://www.example.com/'
    tg_bot = mock_bot.MockTelegramBot(self.config)
    self.db = store.create_store_factory_for_sqlite_db(self.config).create()
    self.tg_setup = integrator.TelegramSetup(
      self.config, self.db, scheduler=None, tg_bot=tg_bot
    )
    self.tg_setup._start_periodic_fetching = mock.MagicMock(return_value=None)
    self.server = server.MessageServer(
      self.config, port=8889, telegram_setup=self.tg_setup
    )
    with open(self.UPDATES_FILE, 'r') as fp:
      self.update = json.load(fp)['result'][0]
    super().setUp()

  def get_app(self):
    return self.server.make_app()

  def test_webhook(self):
    response = self.fetch(
      webhook.TelegramWebhook.ROUTE,
      method='POST',
      body=json.dumps(self.update),
      headers={"Host": "149.154.160.0"},
    )
    self.assertEqual(response.code, 200)
    self.assertFalse(self.tg_setup.queue.empty())

  def test_webhook_from_wrong_host(self):
    response = self.fetch(
      webhook.TelegramWebhook.ROUTE,
      method='POST',
      body=json.dumps(self.update),
      headers={"Host": "89.145.160.0"},
    )
    self.assertEqual(response.code, 404)

  def test_webhook_in_non_webhook_mode(self):
    self.config.server.base_url = 'http://localhost:8787/'
    self.server = server.MessageServer(
      self.config, port=8889, telegram_setup=self.tg_setup
    )
    response = self.fetch(
      webhook.TelegramWebhook.ROUTE,
      method='POST',
      body=json.dumps(self.update),
      headers={"Host": "149.154.160.0"},
    )
    # TODO(olivier): make sure it is 404 here.
    self.assertEqual(response.code, 200)