import collections
from icubam.backoffice.handlers.base import BaseHandler

import tornado.web
from icubam import icu_tree


def make_info(count, label, icon, color):
  return {'label': label, 'count': count, 'icon': icon, 'color': color}


def build_data(icus, bedcounts, num_users):
  tree = icu_tree.ICUTree(level='icu')  # No clustering
  tree.add_many(icus, bedcounts)
  result = []
  result.append(
    make_info(len(icus), 'icus', 'hospital-symbol', 'primary'))
  result.append(
    make_info(num_users, 'users', 'user-md', 'secondary'))

  keys = ['occ', 'free', 'death', 'healed']
  labels = ['Occupied', 'Free', 'deceased', 'Healed']
  icons = ['bed', 'check', 'times', 'chart-line']
  colors = ['info', 'success', 'danger', 'warning']
  for key, lab, i, c in zip(keys, labels, icons, colors):
    result.append(make_info(getattr(tree, key, 0), lab, i, c))
  return result


class HomeHandler(BaseHandler):
  ROUTE = '/'

  @tornado.web.authenticated
  def get(self):
    data = dict()
    if not self.user.is_admin:
      data['Managed'] = build_data(
          self.db.get_managed_icus(self.user.user_id),
          self.db.get_visible_bed_counts_for_user(self.user.user_id),
          len(self.db.get_managed_users(self.user.user_id)))
    data['Overall'] = build_data(
        self.db.get_icus(),
        self.db.get_latest_bed_counts(),
        len(self.db.get_users()))
    return self.render("home.html", data=data)
