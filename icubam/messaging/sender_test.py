import tornado.testing
import tornado.queues

from icubam import config
from icubam.db import store
from icubam.messaging import sender
from icubam.messaging import message
from icubam.messaging.telegram import mock_bot


class SenderTest(tornado.testing.AsyncTestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.db = store.create_store_factory_for_sqlite_db(self.config).create()
    self.queue = tornado.queues.Queue()
    self.admin = self.db.add_default_admin()
    icu_id = self.db.add_icu(self.admin, store.ICU(name='icu1'))
    self.icu = self.db.get_icu(icu_id)
    self.bot = mock_bot.MockTelegramBot(self.config)
    self.sender = sender.Sender(
      self.config, self.db, self.queue, tg_bot=self.bot
    )

  @tornado.testing.gen_test
  async def test_send_missing_data(self):
    """In this test, the user uses neither email, telegram or sms."""
    user_id = self.db.add_user_to_icu(
      self.admin, self.icu.icu_id, store.User(name='user1')
    )
    user = self.db.get_user(user_id)
    msg = message.Message(self.icu, user, 'some_url')
    self.assertFalse(await self.sender.send(msg, user))

  @tornado.testing.gen_test
  async def test_send_sms(self):
    """In this test, the user uses neither email, telegram or sms."""
    user_id = self.db.add_user_to_icu(
      self.admin, self.icu.icu_id,
      store.User(name='user1', telephone='32121312')
    )
    user = self.db.get_user(user_id)
    msg = message.Message(self.icu, user, 'some_url')
    self.assertTrue(await self.sender.send(msg, user))

  @tornado.testing.gen_test
  async def test_send_email(self):
    """In this test, the user uses neither email, telegram or sms."""
    user_id = self.db.add_user_to_icu(
      self.admin, self.icu.icu_id,
      store.User(name='user1', email='someone@example.com')
    )
    # Reset the sender allowing SMTP
    self.config.SMTP_HOST = 'some_host'
    self.sender = sender.Sender(
      self.config, self.db, self.queue, tg_bot=self.bot
    )
    user = self.db.get_user(user_id)
    msg = message.Message(self.icu, user, 'some_url')
    self.assertTrue(await self.sender.send(msg, user))

  @tornado.testing.gen_test
  async def test_send_bot(self):
    """In this test, the user uses neither email, telegram or sms."""
    user_id = self.db.add_user_to_icu(
      self.admin, self.icu.icu_id,
      store.User(name='user1', telegram_chat_id='65451')
    )
    user = self.db.get_user(user_id)
    url = 'some_url'
    msg = message.Message(self.icu, user, url)
    self.assertTrue(await self.sender.send(msg, user))
    self.assertGreater(len(self.bot.client.requests), 0)
    self.assertIn(url, self.bot.client.requests[-1].body.decode())