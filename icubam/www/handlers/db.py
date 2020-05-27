import os

from absl import logging  # noqa: F401

from icubam.db import store
from icubam.analytics import operational_dashboard
from icubam.www.handlers import base


class OperationalDashboardHandler(base.APIKeyProtectedHandler):

  ROUTE = '/dashboard'
  # Problably better not to be equal to admin.
  BACKOFFICE_PREFIX = 'static_bo/'
  API_COOKIE = 'api'
  ACCESS = [store.AccessTypes.STATS, store.AccessTypes.ALL]

  @base.authenticated(code=503)
  def get(self):
    """Serves a page with a table gathering current bedcount data with some extra information."""
    arg_region = self.get_query_argument('region', default=None)
    locale = self.get_user_locale()
    kwargs = operational_dashboard.make(
      self.current_user.external_client_id,
      self.db,
      arg_region,
      locale,
      self.config.analytics.extra_plots_dir,
      external=True
    )

    parent_path = '/'.join(os.path.split(self.PATH)[:-1])
    template_folder = os.path.join('/', parent_path, 'backoffice/templates/')
    return self.render(
      os.path.join(template_folder, 'operational-dashboard.html'),
      backoffice_root=self.BACKOFFICE_PREFIX,
      api_key=self.get_query_argument('API_KEY', None),
      **kwargs
    )
