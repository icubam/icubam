from icubam.backoffice.handlers.base import BaseBOHandler

import tornado.web

class HomeBOHandler(BaseBOHandler):
  ROUTE = '/'

  @tornado.web.authenticated
  def get(self):
    # This is an authenticated handler, so Tornado will redirect to the login
    # page if no cookie is set
    return self.render("home.html")
