from icubam.backoffice.handlers.base import BaseHandler

import tornado.web

class HomeHandler(BaseHandler):
  ROUTE = '/'

  @tornado.web.authenticated
  def get(self):
    # This is an authenticated handler, so Tornado will redirect to the login
    # page if no cookie is set.
    return self.render("home.html")
