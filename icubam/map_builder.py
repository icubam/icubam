from absl import logging
import os.path
from typing import List, Dict

from icubam.db import store


def get_color(value):
  color = 'red'
  if value < 0.5:
    color = 'green'
  elif value < 0.8:
    color = 'orange'
  return color


class ICUTree:
  """Represent a hierarchical clustering of icus per political region."""

  # CLUSTER_KEY = 'dept'  # city
  LEVELS = ['country', 'region', 'dept', 'icu']

  def __init__(self, level='country'):
    self.id = None
    self.label = None
    self.level = level
    self.phone = None
    self.occ = 0
    self.free = 0
    self.total = 0
    self.ratio = 0
    self.lat = 0.0
    self.long = 0.0
    self.color = get_color(self.ratio)
    self.children = dict()

  def get_level_name(self, bedcount, level = None):
    level = self.level if level is None else level
    icu = bedcount.icu
    name = getattr(icu, level, None)
    if level == 'region':
      name = name.name
    return name if name is not None else level

  def get_next_level(self):
    idx = self.LEVELS.index(self.level)
    if idx < len(self.LEVELS) - 1:
      return self.LEVELS[idx + 1]
    return None

  def add(self, bedcount):
    if self.label is None:
      self.label = self.get_level_name(bedcount)
      self.id = 'id_{}'.format(self.label.replace(' ', '_'))
    if bedcount.n_covid_occ:
      self.occ += bedcount.n_covid_occ
    if bedcount.n_covid_free:
      self.free += bedcount.n_covid_free
    self.total = self.occ + self.free
    self.ratio = self.occ / self.total if (self.total > 0) else 0
    self.color = get_color(self.ratio)
    next_level = self.get_next_level()
    if next_level is not None:
      next_level_name = self.get_level_name(bedcount, next_level)
      child = self.children.get(next_level_name, ICUTree(next_level))
      child.add(bedcount)
      if next_level_name not in self.children:
        self.children[next_level_name] = child
        n = len(self.children)
        self.lat = (child.lat + (n - 1)*self.lat) / n
        self.long = (child.long + (n - 1)*self.long) / n
    elif self.phone is None:
      self.phone = bedcount.icu.telephone.lstrip('+')
      self.lat = bedcount.icu.lat
      self.long = bedcount.icu.long

  def extract_at(self, level, nodes):
    if self.level == level:
      nodes.append(self)
    else:
      for child in self.children.values():
        child.extract_at(level, nodes)


class MapBuilder:

  def __init__(self, config, db, popup_template):
    self.config = config
    self.db = db
    self.popup_template = popup_template

  def to_map_data(self, tree, level):
    nodes = []
    tree.extract_at(level, nodes)
    result = []
    for node in nodes:
      views = [
        {'name': 'cluster', 'beds': [node]},
        {
          'name': 'full',
          'beds': sorted(node.children.values(), key=lambda x: x.label)},
      ]
      popup = self.popup_template.generate(
        cluster=node.label, color=node.color, views=views)
      curr = {'popup': popup.decode()}
      for key in ['id', 'label', 'lat', 'long', 'color', 'free']:
        curr[key] = getattr(node, key, None)
      result.append(curr)

    # This sorts the from north to south, so as to avoid overlap on the north.
    result.sort(key=lambda x: x['lat'], reverse=True)
    return result

  def prepare_json(self, user_id=None, center_icu=None, level='dept'):
    bedcounts = self.db.get_visible_bed_counts_for_user(
      user_id, force=user_id is None)
    tree = ICUTree()
    for bedcount in bedcounts:
      tree.add(bedcount)

    data = self.to_map_data(tree, level)
    anchor = center_icu if center_icu is not None else tree
    center = {'lat': anchor.lat, 'lng': anchor.long}
    return data, center
