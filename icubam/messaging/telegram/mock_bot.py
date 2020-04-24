from icubam.messaging.telegram import bot


class MockTelegramBot(bot.TelegramBot):
  def __init__(self, config):
    config.TELEGRAM_API_KEY = 'key'
    config.messaging.telegram_bot = 'michel'
    super().__init__(config)
    self.posts = []

  async def post(self, data, route):
    self.posts.append((data, route))

  async def getUpdates(self, min_id=0):
    return []
