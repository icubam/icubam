from backoffice.www.handlers.base import BaseBOHandler


class LoginHandler(BaseBOHandler):

  ROUTE= "/login"

  def get(self):
    self.write('<html><body><form action="/login" method="post">'
               'Name: <input type="text" name="name">'
               '<input type="submit" value="Sign in">'
               '</form></body></html>')

  def post(self):
    self.set_secure_cookie("user", self.get_argument("name"))
    self.redirect("/")

class AuthLogoutHandler(BaseBOHandler):
  def get(self):
    self.clear_cookie("user")
    self.redirect(self.get_argument("next", "/"))