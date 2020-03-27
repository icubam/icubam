from icubam.www.handlers import base


class ErrorHandler(base.BaseHandler):
  ROUTE = '/error'

  def prepare(self):
    self.set_status(404)
    self.render("error.html")
