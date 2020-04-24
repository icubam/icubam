import tornado.queues
from icubam.messaging.handlers import telegram_webhook as webhook
from icubam.messaging.telegram import bot, updater


class TelegramSetup:
  """Sets up the telegram in the server support depending on the config."""
  def __init__(self, config, db, scheduler=None):
    self.config = config
    self.queue = tornado.queues.Queue()
    self.bot = bot.TelegramBot(config)
    self.processor = updater.UpdateProcessor(config, db, self.queue, scheduler)
    self.fetcher = updater.UpdateFetcher(config, self.queue)

  @property
  def uses_webhook(self):
    url = self.config.server.base_url
    return 'https' in url and 'localhost' not in url

  @property
  def is_on(self):
    msg_config = self.config.messaging
    return (
      msg_config.has_key('telegram_bot') and
      msg_config.has_key('telegram_updates_every') and
      self.config.TELEGRAM_API_KEY is not None
    )

  def setup_fetching(self, callbacks):
    """If Telegram should be running, we either setup a webhook or
    starts fetching regularly the updates depending on the configuration."""
    if not self.is_on:
      return

    callbacks.append(self.processor.process)
    if self.uses_webhook:
      callbacks.append(self.bot.setWebhook)
    else:
      repeat_every = self.config.messaging.telegram_updates_every * 1000
      tornado.ioloop.PeriodicCallback(self.fetcher.fetch, repeat_every).start()

  def add_routes(self, app_routes):
    """Ads the proper routes for telegram, restricting for proper subnets."""
    if not self.is_on or not self.uses_webhook:
      return

    routes = [(
      webhook.TelegramWebhook.ROUTE, webhook.TelegramWebhook, {
        'queue': self.queue
      }
    )]
    app_routes.append(
      (tornado.routing.HostMatches(webhook.TelegramWebhook.HOSTS), routes)
    )
