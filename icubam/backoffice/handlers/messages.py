import logging
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store
from icubam.messaging import client


class ListMessagesHandler(base.AdminHandler):

  ROUTE = "/list_messages"

  def initialize(self, config, db):
    super().initialize(config, db)
    self.client = client.MessageServerClient(config)

  @tornado.web.authenticated
  async def get(self):
    try:
      messages = await self.client.get_scheduled_messages()
    except Exception as e:
    data = [self.format_list_item(msg) for msg in messages]
    self.render(
        "list.html", data=data, objtype='Acces Tokens',
        create_route=TokenHandler.ROUTE)
