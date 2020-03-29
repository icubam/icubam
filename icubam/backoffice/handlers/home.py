from icubam.backoffice.handlers.base import BaseBOHandler


class HomeBOHandler(BaseBOHandler):
  ROUTE = '/'

  def get(self):
    return self.render("home.html")
