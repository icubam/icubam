import tornado.escape

from icubam.backoffice.handlers.base import BaseHandler


class LoginHandler(BaseHandler):

  ROUTE = "login"

  def get(self, error=""):
    # User already logged in, just redirect to the home.
    if self.get_current_user():
      return self.redirect(self.get_argument("next", self.root_path))

    error = self.get_argument("error", None)
    return self.render("login.html", error=error)

  def post(self):
    self.error = None
    email = self.get_body_argument("email", "")
    password = self.get_body_argument("password", "")
    userid = self.db.auth_user(email, password)
    if userid is not None:
      self.set_secure_cookie(self.COOKIE, tornado.escape.json_encode(userid))
      return self.redirect(self.get_argument("next", self.root_path))

    return self.redirect("{}?error=true".format(self.ROUTE))
