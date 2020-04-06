import datetime
import logging
import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base, home, icus, users
from icubam.db import store
from icubam.messaging import client


class ListMessagesHandler(base.AdminHandler):

  ROUTE = "list_messages"

  def initialize(self):
    super().initialize()
    self.client = client.MessageServerClient(self.config)

  def prepare_for_table(self, msg):
    result = [
      {
        'key': 'user',
        'value': msg['user_name'],
        'link': f'{users.UserHandler.ROUTE}?id={msg["user_id"]}'
      },
      {
        'key': 'ICU',
        'value': msg["icu_name"],
        'link': f'{icus.ICUHandler.ROUTE}?id={msg["icu_id"]}'
      },
    ]
    msg_dict = {}
    msg_dict['telephone'] = msg['phone']
    msg_dict['scheduled'] ='{0:%Y/%m/%d at %H:%M:%S}'.format(
        datetime.datetime.fromtimestamp(msg['when']))
    msg_dict['attempts'] = msg['attempts']
    msg_dict['first sent'] = 'not yet'
    if msg['first_sent'] is not None:
      msg_dict['first sent'] = '{0:%Y/%m/%d at %H:%M:%S}'.format(
        datetime.datetime.fromtimestamp(msg['first_sent']))
    result.extend(self.format_list_item(msg_dict))
    result.append({
      'key': 'url',
      'value': 'link',
      'link': msg['url']
    })
    return result

  @tornado.web.authenticated
  async def get(self):
    try:
      messages = await self.client.get_scheduled_messages(self.user.user_id)
    except Exception as e:
      logging.error(f'Cannot contact message server: {e}')
      return self.redirect(self.root_path)

    data = [self.prepare_for_table(msg) for msg in messages]
    self.render_list(
      data=data, objtype='Scheduled Messages', create_handler=None)
