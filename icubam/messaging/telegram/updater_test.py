import tornado.queues
import tornado.testing

from icubam import config
from icubam.db import store
from icubam.www import token
from icubam.messaging.telegram import updater
from icubam.messaging.telegram import mock_bot


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
    example_update = {
      'update_id': 372570010,
      'message': {
        'message_id': 19,
        'from': {
          'id': 170497,
          'is_bot': False,
          'first_name': 'Olivier',
          'language_code': 'fr'
        },
        'chat': {
          'id': 170497,
          'first_name': 'Olivier',
          'type': 'private'
        },
        'date': 1587576957,
        'text': '/start something',
        'entities': [{
          'offset': 0,
          'length': 6,
          'type': 'bot_command'
        }]
      }
    }
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

    # TODO(olivier): use authenticator here.
    token_encoder = token.TokenEncoder(self.config)
    jwt = token_encoder.encode_data(user, icu)
    example_update['message']['text'] = f'/start {jwt}'
    await self.processor.process_update(example_update)
    self.assertGreater(len(self.processor.bot.client.requests), 0)
    msg_json = self.processor.bot.client.requests[-1].body
    self.assertIn('registered', msg_json.decode())


if __name__ == '__main__':
  tornado.testing.main()