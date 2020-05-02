import json
import tornado.queues
import tornado.testing

from icubam import config
from icubam.db import store
from icubam.www import token
from icubam.messaging.telegram import updater
from icubam.messaging.telegram import mock_bot

UPDATES_FILE = 'resources/test/telegram_updates.json'


class UpdateFetcherTest(tornado.testing.AsyncTestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.queue = tornado.queues.Queue()
    self.fetcher = updater.UpdateFetcher(
      self.config, self.queue, mock_bot.MockTelegramBot(self.config)
    )

  @tornado.testing.gen_test
  async def test_fetch(self):
    with open(UPDATES_FILE, 'r') as fp:
      self.fetcher.bot.client.set_body(json.load(fp))

    await self.fetcher.fetch()
    self.assertGreater(self.fetcher.last_update_id, 0)
    self.assertFalse(self.queue.empty())

  @tornado.testing.gen_test
  async def test_fetch_fail(self):
    self.fetcher.bot.code = 404
    self.assertIsNone(await self.fetcher.fetch())
    self.assertEqual(self.fetcher.last_update_id, 0)
    self.assertTrue(self.queue.empty())


class UpdateProcessorTest(tornado.testing.AsyncTestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    factory = store.create_store_factory_for_sqlite_db(self.config)
    self.db = factory.create()
    self.queue = tornado.queues.Queue()
    self.processor = updater.UpdateProcessor(
      self.config, self.db, self.queue, None,
      mock_bot.MockTelegramBot(self.config)
    )

  @tornado.testing.gen_test
  async def test_process_update(self):
    with open(UPDATES_FILE, 'r') as fp:
      data = json.load(fp)
    example_update = data['result'][0]
    # This should lead to a unknown user.
    await self.processor.process_update(example_update)
    self.assertGreater(len(self.processor.bot.client.requests), 0)
    msg_json = self.processor.bot.client.requests[-1].body
    self.assertIn('Cannot identify', msg_json.decode())

    # Now makes a real user and pass a token along
    admin_id = self.db.add_default_admin()
    icu_id = self.db.add_icu(admin_id, store.ICU(name='icu'))
    icu = self.db.get_icu(icu_id)
    user_id = self.db.add_user_to_icu(
      admin_id, icu_id, store.User(name='patrick')
    )
    user = self.db.get_user(user_id)

    # TODO(olivier): use authenticator here when available.
    token_encoder = token.TokenEncoder(self.config)
    jwt = token_encoder.encode_data(user, icu)
    example_update['message']['text'] = f'/start {jwt}'
    await self.processor.process_update(example_update)
    self.assertGreater(len(self.processor.bot.client.requests), 0)
    msg_json = self.processor.bot.client.requests[-1].body
    self.assertIn('registered', msg_json.decode())


if __name__ == '__main__':
  tornado.testing.main()
