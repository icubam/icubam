import tornado.escape

from icubam.backoffice.handlers.base import BaseHandler


class LoginHandler(BaseHandler):

  ROUTE = "/login"

  def _makeErrorMessage(self, error):
    return "?error={}".format(error)

  def authenticate(self, email, password):
    if not email:
      return None, "Email not provided"
    if not password:
      return None, "Password not provided"

    userid = self.db.auth_user(email, password)
    if not userid or userid < 0:
      return None, "Authentication failed"

    return userid, ""

  def get(self):
    # User already logged in, just redirect to the home.
    if self.get_current_user():
      return self.redirect(self.get_argument("next", "/"))
    return self.render("login.html", error=self.get_argument("error", ""))

  def post(self):
    userid, error = self.authenticate(
      self.get_argument("email", ""), self.get_argument("password", ""))
    if userid:
      self.set_secure_cookie(self.COOKIE, tornado.escape.json_encode(userid))
      return self.redirect(self.get_argument("next", "/"))

    # Failed to login, GET page again with the error message.
    return self.redirect(self.ROUTE + self._makeErrorMessage(error))
