import os
import sys
from subprocess import check_output
from typing import Dict, List, Iterable, Optional, Callable
import traceback

import tornado.web

import icubam
from icubam.www.handlers import base
from icubam.www import updater


def _try_call(func: Callable, *args, **kwargs) -> Optional[str]:
  """Try to call a funcion and store exception if it occurs.

  Parameters
  ----------
  func: callable
    the function to run

  Returns
  -------
  str or None:
     the error message, or None if there is no error.
  """
  try:
    func()
  except Exception:
    exc_type, exc_value, tb = sys.exc_info()
    tb_msg = traceback.format_tb(tb)
    return f'{tb_msg}\n{exc_type.__name__}: {exc_value}'


class VersionHandler(base.BaseHandler):
  ROUTE = '/version'

  def initialize(self, config, db):
    super().initialize(config, db)
    self.updater = updater.Updater(self.config, self.db)

  def get_data(self) -> List[Dict]:
    """Get sanity checks data"""
    package = {}
    package['version'] = icubam.__version__
    try:
      git_hash = check_output(['git', 'rev-parse', '--short', 'HEAD'],
                              encoding='utf-8').strip()
    except Exception:
      git_hash = 'NA'
    package['git-hash'] = git_hash

    errors = {}

    for method in [
      'get_icus', 'get_users', 'get_bed_counts', 'get_admins', 'get_regions'
    ]:
      func = getattr(self.db, method)
      msg = _try_call(func)
      if msg is not None:
        errors[method] = msg

    return {'package': package, 'errors': errors}

  @tornado.web.authenticated
  def get(self):
    self.write({"data": self.get_data()})
