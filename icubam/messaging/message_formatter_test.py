import itertools

from absl.testing import absltest

from icubam import config
from icubam.db import store
from icubam.messaging import message_formatter
from icubam.messaging import message


class MessageFormatterTest(absltest.TestCase):
  def setUp(self):
    super().setUp()
    self.config = config.Config('resources/test.toml')
    self.db = store.create_store_factory_for_sqlite_db(self.config).create()
    self.formatter = message_formatter.MessageFormatter()
    self.admin_id = self.db.add_default_admin()
    self.icu_id = self.db.add_icu(self.admin_id, store.ICU(name='rea'))
    self.icu = self.db.get_icu(self.icu_id)
    self.user_id = self.db.add_user_to_icu(
      self.admin_id, self.icu_id, store.User(name='user')
    )
    self.user = self.db.get_user(self.user_id)

  def test_format(self):
    url = 'some url'
    msg = message.Message(self.icu, self.user, url)
    self.formatter.format(msg)
    self.assertNotEmpty(msg.text)
    self.assertNotEmpty(msg.html)
    to_be_tested = itertools.product([url, self.user.name, self.icu.name],
                                     [msg.text, msg.html])
    for item, text in to_be_tested:
      self.assertContainsSubsequence(text, item)


if __name__ == '__main__':
  absltest.main()
