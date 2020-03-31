import os
from subprocess import check_output
from typing import Dict, List, Iterable

import tornado.web

import icubam
from icubam.www.handlers import base
from icubam.www import updater


def _agg_iterable(x: Iterable, attr: str, agg=sum):
  """For each item in an iterable, get an attribute and aggregate

  Example
  -------
  >>> from collections import namedtuple
  >>> Obj = namedtuple('Obj', ('a', 'b'))
  >>> Obj(1, 2)
  Obj(a=1, b=2)
  >>> x = [Obj(1, 2), Obj(5, 4)]
  >>> _agg_iterable(x, 'a', sum)
  6
  """
  return agg([getattr(el, attr) for el in x])


class SanityChecksHandler(base.BaseHandler):
  ROUTE = '/sanity-checks'

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

    db_stats = {}

    db_stats['icus.count'] = len(self.db.get_icus())

    bedcounts = self.db.get_bed_counts()
    # compute aggregated bed counts
    db_stats['bed_counts.count'] = len(bedcounts)
    for key in ['n_covid_occ', 'n_covid_free']:
      db_stats[f'bed_counts.{key}'] = _agg_iterable(bedcounts, key, agg=sum)

    db_stats['users.count'] = len(self.db.get_users())
    db_stats['users.is_admin.count'] = len(self.db.get_admins())
    db_stats['regions.count'] = len(self.db.get_regions())

    server = {}
    try:
      server['load-average'] = list(os.getloadavg())
    except OSError:  # not a Unix system
      pass

    return {'package': package, 'db': db_stats, 'server': server}

  @tornado.web.authenticated
  def get(self):
    self.write({"data": self.get_data()})
