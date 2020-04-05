import sys
from subprocess import check_output
from typing import Dict, List, Optional, Callable
import traceback

import tornado.web

import icubam
from icubam.www.handlers import base
from icubam.www import updater


class VersionHandler(base.BaseHandler):
  ROUTE = '/version'

  def initialize(self, config, db_factory):
    super().initialize(config, db_factory)
    self.updater = updater.Updater(self.config, self.db)

  def get_data(self) -> List[Dict]:
    """Get sanity checks data"""
    data = {}
    data['version'] = icubam.__version__
    try:
      git_hash = check_output(['git', 'rev-parse', '--short', 'HEAD'],
                              encoding='utf-8').strip()
    except Exception:
      git_hash = 'NA'
    data['git-hash'] = git_hash
    bed_counts = self.db.get_bed_counts()
    last_modified = max([el.last_modified for el in bed_counts], default='NA')
    data['bed_counts.last_modified'] = str(last_modified)
    return data

  def get(self):
    self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
    self.write({"data": self.get_data()})
