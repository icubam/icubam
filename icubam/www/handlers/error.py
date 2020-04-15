from icubam.www.handlers import base


class ErrorHandler(base.BaseHandler):
  ROUTE = '/error'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)

  def get(self):
    return self.render('error.html')
