import tornado.escape
import tornado.web

from icubam.backoffice.handlers import base
from icubam.backoffice.handlers import home
from icubam.db import store


class ListBedCountsHandler(base.BaseHandler):
  ROUTE = '/dashboard'

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
