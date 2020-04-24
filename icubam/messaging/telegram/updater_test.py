import tornado.queues
import tornado.testing

from icubam import config
from icubam.db import store
from icubam.messaging.telegram import updater
from icubam.messaging.telegram import mock_bot


class UpdateFetcherTest(tornado.testing.AsyncTestCase):
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
    await self.processor.process_update(example_update)


if __name__ == '__main__':
  tornado.testing.main()