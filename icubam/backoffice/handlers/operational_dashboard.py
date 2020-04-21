import tornado.web
from icubam.backoffice.handlers import base
from icubam.predicu import operational_dashboard


class OperationalDashHandler(base.AdminHandler):
  ROUTE = 'operational-dashboard'

  @tornado.web.authenticated
  def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    arg_region = self.get_query_argument('region', default=None)
    locale = self.get_user_locale()
    kwargs = operational_dashboard.make(
      self.current_user.user_id, self.db, arg_region, locale,
      self.config.backoffice.extra_plots_dir
    )
    return self.render(
      "operational-dashboard.html",
      backoffice_root=self.config.backoffice.root,
      api_key=None,
      **kwargs
    )
