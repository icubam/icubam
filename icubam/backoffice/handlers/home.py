from icubam.backoffice.handlers.base import BaseBOHandler


class HomeBOHandler(BaseBOHandler):
  ROUTE = '/'

  def get(self):
    self.render("home.html")
