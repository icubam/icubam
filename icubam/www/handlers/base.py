import tornado.web


class BaseHandler(tornado.web.RequestHandler):
  """A base class for handlers."""

  COOKIE = 'id'

  def get_template_path(self):
    return 'icubam/www/templates/'

  def get_current_user(self):
    return self.get_secure_cookie(self.COOKIE)

  def write_error(self, status_code, **kwargs):
    print("status {} {}".format(status_code, kwargs))
    if status_code == 404:
      self.render("404.html")
    else:
      self.render("error.html", **{"status_code": status_code, "message": kwargs["exc_info"][1].log_message})
