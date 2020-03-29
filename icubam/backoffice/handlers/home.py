from icubam.backoffice.handlers.base import BaseBOHandler


class HomeBOHandler(BaseBOHandler):
  ROUTE = '/'

  def get(self):
    if self.get_current_user():
      return self.render("home.html")

    # No user logged in, redirects to the login page.
    return self.redirect("/login")
