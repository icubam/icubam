import tornado

from icubam.www.handlers import base


class ErrorHandler(base.BaseHandler):

  def prepare(self):
    raise tornado.web.HTTPError(404)
