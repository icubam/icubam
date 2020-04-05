import datetime
import logging
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store
from icubam.messaging import client


class ListMessagesHandler(base.AdminHandler):

  ROUTE = "/list_messages"

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.client = client.MessageServerClient(config)

  def prepare_for_table(self, msg):
    msg['when'] = '{0:%Y/%m/%d at %H:%M:%S}'.format(
      datetime.datetime.fromtimestamp(msg['when']))
    return self.format_list_item(msg)

  @tornado.web.authenticated
  async def get(self):
    try:
      messages = await self.client.get_scheduled_messages(self.user.user_id)
    except Exception as e:
      logging.error(f'Cannot contact message server: {e}')
      return self.redirect('/')

    data = [self.prepare_for_table(msg) for msg in messages]
    self.render(
        "list.html", data=data, objtype='Scheduled Messages', create_route=None)
