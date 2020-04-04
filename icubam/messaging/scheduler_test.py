from absl.testing import absltest
from datetime import datetime
import tornado.testing
from unittest import mock

from icubam.db import store
from icubam.messaging import scheduler
from icubam.messaging import message
from icubam import config


fake_now = datetime(2020, 3, 31, 12, 21).timestamp()


class MockQueue:
  def __init__(self):
    self.data = []

  async def put(self, data):
    self.data.append(data)


class SchedulerTestCase(tornado.testing.AsyncTestCase):

  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.db = store.create_store_for_sqlite_db(self.config)
    self.queue = MockQueue()
    self.scheduler = scheduler.MessageScheduler(
      self.config, self.db, self.queue)

    self.admin = self.db.add_default_admin()
    self.icu_id = self.db.add_icu(self.admin, store.ICU(name='my_icu'))

    user = store.User(name='michel', telephone='1234')
    self.user_id = self.db.add_user_to_icu(self.admin, self.icu_id, user)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  def test_computes_delay(self):
    delay = self.scheduler.computes_delay(None)
    self.assertEqual(delay, 9 * 60)
    delay = 10
    self.assertEqual(delay, self.scheduler.computes_delay(delay))
    self.scheduler.when = False
    delay = self.scheduler.computes_delay(None)
    self.assertEqual(delay, -1)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  def test_schedule_message(self):
    user = self.db.get_user(self.user_id)
    icu = self.db.get_icu(self.icu_id)
    msg = message.Message(icu, user, url='url')
    self.assertEqual(len(self.scheduler.timeouts), 0)
    delay = 100
    success = self.scheduler.schedule_message(msg, delay=delay)
    self.assertTrue(success)
    self.assertEqual(len(self.scheduler.timeouts), 1)
    key = user.user_id, icu.icu_id
    timeout = self.scheduler.timeouts.get(key, None)
    self.assertIsNotNone(timeout)
    self.assertTrue(timeout.when, fake_now + delay)

    # another message with smaller delay: in
    offset = -2
    success = self.scheduler.schedule_message(msg, delay=delay+offset)
    self.assertTrue(success)
    timeout = self.scheduler.timeouts.get(key, None)
    self.assertIsNotNone(timeout)
    self.assertTrue(timeout.when, fake_now + delay + offset)

    # another message with negative delay
    success = self.scheduler.schedule_message(msg, delay=-1)
    self.assertFalse(success)

    # Another user same icu: another entry
    user = store.User(name='jacqueline', telephone='12333')
    userid = self.db.add_user_to_icu(self.admin, icu.icu_id, user)
    user = self.db.get_user(userid)
    icu = self.db.get_icu(self.icu_id)
    offset = 100
    msg2 = message.Message(icu, user, url='url')
    success = self.scheduler.schedule_message(msg2, delay=delay+offset)
    self.assertTrue(success)
    self.assertEqual(len(self.scheduler.timeouts), 2)

    # Same user new icu: new entry
    icuid = self.db.add_icu(self.admin, store.ICU(name='anothericu'))
    self.db.assign_user_to_icu(self.admin, userid, icuid)
    user = self.db.get_user(userid)
    icu = self.db.get_icu(icuid)
    msg3 = message.Message(icu, user, url='url')
    success = self.scheduler.schedule_message(msg3, delay=delay+offset)
    self.assertTrue(success)
    self.assertEqual(len(self.scheduler.timeouts), 3)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  def test_schedule(self):
    user = self.db.get_user(self.user_id)
    icu = self.db.get_icu(self.icu_id)
    self.assertEqual(len(self.scheduler.timeouts), 0)
    delay = 200
    success = self.scheduler.schedule(user, icu, delay=delay)
    self.assertTrue(success)
    self.assertEqual(len(self.scheduler.timeouts), 1)

    # New user, in icu
    user1 = store.User(name='jacqueline', telephone='12333')
    userid1 = self.db.add_user_to_icu(self.admin, self.icu_id, user1)
    user1 = self.db.get_user(userid1)
    icu = self.db.get_icu(self.icu_id)
    success = self.scheduler.schedule(user1, icu, delay=delay)
    self.assertTrue(success)
    self.assertEqual(len(self.scheduler.timeouts), 2)

    # New user, not in icu
    user2 = store.User(name='armand', telephone='127313')
    userid2 = self.db.add_user(user2)
    user2 = self.db.get_user(userid2)
    icu = self.db.get_icu(self.icu_id)
    success = self.scheduler.schedule(user2, icu, delay=delay)
    self.assertFalse(success)
    self.assertEqual(len(self.scheduler.timeouts), 2)

    # New user, in icu but not active
    user3 = store.User(name='armande', telephone='15313', is_active=False)
    userid3 = self.db.add_user_to_icu(self.admin, self.icu_id, user3)
    user3 = self.db.get_user(userid3)
    icu = self.db.get_icu(self.icu_id)
    success = self.scheduler.schedule(user3, icu, delay=delay)
    self.assertFalse(success)
    self.assertEqual(len(self.scheduler.timeouts), 2)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  def test_schedule_all(self):
    names = ['armand', 'patrick', 'bernard', 'mathilde']
    for name in names:
      curr = store.User(name=name, telephone=name, is_active=True)
      userid = self.db.add_user_to_icu(self.admin, self.icu_id, curr)

    users = self.db.get_users()
    self.scheduler.schedule_all()
    # We are not sure about what is the db. But at least it should send to the
    # newly built users.
    # TODO(olivier): do better here
    self.assertGreater(len(self.scheduler.timeouts), len(names) + 1)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  def test_schedule_all(self):
    self.assertGreater(len(self.scheduler.messages), 0)

  @mock.patch('time.time', mock.MagicMock(return_value=fake_now))
  @tornado.testing.gen_test
  async def test_do_send(self):
    icu = self.db.get_icu(self.icu_id)
    user = self.db.get_user(self.user_id)
    msg = message.Message(icu, user, url='url')
    await self.scheduler.do_send(msg)
    # response = self.wait()
    self.assertEqual(len(self.queue.data), 1)
    self.assertEqual(msg.first_sent, fake_now)
    self.assertEqual(msg.attempts, 1)
    self.assertEqual(len(self.scheduler.timeouts), 1)
    timeout = self.scheduler.timeouts.get(msg.key, None)
    self.assertIsNotNone(timeout)
    self.assertEqual(timeout.when, self.scheduler.reminder_delay + fake_now)


if __name__ == '__main__':
  absltest.main()
