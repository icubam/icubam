from absl import logging
import os.path
import tornado.escape
import tornado.web
from typing import Optional

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.www.handlers import home as www_home
from icubam.www.handlers import db as www_db
from icubam.db import store


class ListTokensHandler(base.AdminHandler):

  ROUTE = "list_tokens"

  def prepare_for_table(self, client):
    result = [{
        'key': 'name',
        'value': client.email,
        'link': f'{TokenHandler.ROUTE}?id={client.external_client_id}'}
    ]
    client_dict = dict()
    for key in ['access_key', 'is_active', 'expiration_date']:
      client_dict[key] = getattr(client, key, None)
    result.extend(self.format_list_item(client_dict))
    for handler in [www_home.MapByAPIHandler, www_db.DBHandler]:
      route = handler.ROUTE.strip('/').split('/')[0]
      if handler == www_db.DBHandler:
        route += '/bedcounts'
      args = f'?API_KEY={client.access_key}'
      url = os.path.join(self.config.server.base_url, route + args)
      result.append({'key': route, 'value': 'link', 'link': url})
    return result

  @tornado.web.authenticated
  def get(self):
    clients = self.db.get_external_clients()
    data = [self.prepare_for_table(client) for client in clients]
    self.render_list(
      data=data, objtype='Acces Tokens', create_handler=TokenHandler)


class TokenHandler(base.AdminHandler):

  ROUTE = "token"

  @tornado.web.authenticated
  def get(self):
    userid = self.get_query_argument('id', None)
    user = None
    if userid is not None:
      user = self.db.get_external_client(userid)
    return self.do_render(user=user, error=False)

  def do_render(self, user: Optional[store.User], error=False):
    user = user if user is not None else store.ExternalClient()
    if user.is_active is None:
      user.is_active = True
    return self.render("token.html", user=user, error=error,
                       list_route=ListTokensHandler.ROUTE)

  @tornado.web.authenticated
  def post(self):
    values = self.parse_from_body(store.ExternalClient)
    values["is_active"] = values.get("is_active", "off") == 'on'
    id_key = 'external_client_id'
    token_id = values.pop(id_key, '')
    try:
      if not token_id:
        token_id = self.db.add_external_client(
          self.user.user_id, store.ExternalClient(**values))
      else:
        self.db.update_external_client(self.user.user_id, token_id, values)
    except Exception as e:
      logging.error(f'cannot save token {e}')
      values[id_key] = token_id
      return self.do_render(store.ExternalClient(**values), error=True)

    return self.redirect(ListTokensHandler.ROUTE)
