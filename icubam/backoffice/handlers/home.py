from tornado_sqlalchemy import SessionMixin

from icubam.backoffice.handlers.base import BaseBOHandler


class HomeBOHandler(SessionMixin, BaseBOHandler):
  ROUTE = '/'

  def get(self):
    self.render("home.html")
