from icubam.backoffice.handlers.base import BaseHandler


class LogoutHandler(BaseHandler):

  ROUTE = "logout"

  def get(self):
    self.clear_cookie(self.COOKIE)
    return self.redirect(self.root_path)
