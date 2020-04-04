import tornado.escape
import tornado.web
from typing import Optional

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store


class ListTokensHandler(base.AdminHandler):

  ROUTE = "/list_tokens"

  @tornado.web.authenticated
  def get(self):
    clients = self.db.get_external_clients()
    data = [self.format_list_item(client.to_dict()) for client in clients]
    self.render(
        "list.html", data=data, objtype='Acces Tokens',
        create_route=TokenHandler.ROUTE)


class TokenHandler(base.AdminHandler):

  ROUTE = "/token"

  @tornado.web.authenticated
  def get(self):
    userid = self.get_query_argument('id', None)
    user = None
    if userid is not None:
      user = self.db.get_external_client(userid)
    self.do_render(user=user)

  def do_render(self, user: Optional[store.User], error=False):
    user = user if user is not None else store.ExternalClient()
    self.render("token.html", user=user, error=error)

  @tornado.web.authenticated
  def post(self):
    values = self.parse_from_body(store.ExternalClient)
    id_key = 'external_client_id'
    token_id = values.pop(id_key, '')
    try:
      if not token_id:
        self.db.add_external_client(
          self.user.user_id, store.ExternalClient(**values))
      else:
        self.db.update_external_client(self.user.user_id, token_id, values)
    except Exception as e:
      logging.error(f'cannot save token {e}')
      values[id_key] = regiontoken_id
      return self.do_render(user=store.ExternalClient(**values), error=True)

    return self.redirect(ListTokensHandler.ROUTE)
