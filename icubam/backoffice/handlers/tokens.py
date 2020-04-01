import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store


class ListTokensHandler(base.BaseHandler):

  ROUTE = "/list_tokens"

  @tornado.web.authenticated
  def get(self):
    if not self.user.is_admin:
      return self.redirect(home.HomeHandler.ROUTE)

    clients = self.store.get_external_clients()
    data = [client.to_dict() for client in clients]
    columns = [] if not data else list(data[0].keys())
    self.render(
        "list.html", data=data, columns=columns, objtype='Acces Tokens',
        create_route=TokenHandler.ROUTE)


class TokenHandler(base.BaseHandler):

  ROUTE = "/token"

  @tornado.web.authenticated
  def get(self):
    if not self.user.is_admin:
      return self.redirect(home.HomeHandler.ROUTE)

    userid = self.get_query_argument('id', None)
    user = None
    if userid is not None:
      user = self.db.get_external_client(userid)

    user = user if user is not None else store.ExternalClient()
    self.render("token.html", user=user, error="")

  @tornado.web.authenticated
  def post(self):
    fields = ['name', 'telephone', 'email']
    values = {k: self.get_body_argument(k, "") for k in fields}
    incoming_user = store.ExternalClient(**values)

    user = self.db.get_external_client_by_email(incoming_user.email)
    if user is None:
      c_id, _ = self.db.add_external_client(self.user.user_id, incoming_user)
      self.redirect("{}?id={}".format(self.ROUTE, c_id))

    else:
      print('now what?')
