import tornado.escape

from icubam.backoffice.handlers.base import BaseBOHandler


class LoginBOHandler(BaseBOHandler):

  ROUTE= "/login"

  def _makeErrorMessage(self, error):
    return "?error={}".format(error)

  def _authenticate(self, email, password):
    # TODO(fpquintao): validate the user in the database.
    return (True, "")

  def get(self):
    # User already logged in, just redirect to the home.
    if self.get_current_user():
      return self.redirect(self.get_argument("next", "/"))
    return self.render("login.html", error=self.get_argument("error", ""))

  def post(self):
    email = self.get_argument("email", "")
    password = self.get_argument("password", "")
    authenticate = self._authenticate(email, password)
    if authenticate[0]:
      self.set_secure_cookie(self.COOKIE, tornado.escape.json_encode(email))
      return self.redirect(self.get_argument("next", "/"))
    # Failed to login, GET page again with the error message.
    return self.redirect("/login" + self._makeErrorMessage(authenticate[1]))
