import os.path

from icubam.www.handlers import base


class DisclaimerHandler(base.BaseHandler):
  ROUTE = '/disclaimer'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)

  def get_disclaimer_html(self):
    """To show a disclaimer page if specified in configuration."""
    path = self.config.server.disclaimer
    if os.path.exists(path):
      with open(path, 'r') as fp:
        return fp.read()

  def get_current_user(self):
    """This route is not secured at first."""
    return None

  async def get(self):
    """Serves the page filled with the configuration specified file."""
    if self.config.server.has_key('disclaimer'):
      html = self.get_disclaimer_html()
      data = {'disclaimer': html}
      self.render('disclaimer.html', **data)
