from absl import logging
import os.path
from typing import List, Dict
import tornado.template

from icubam.db import store
from icubam import icu_tree


class MapBuilder:
  """Builds the necessary data to build an HTML map."""
  PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

  def __init__(self, config, db):
    self.config = config
    self.db = db
    loader = tornado.template.Loader(
      os.path.join(self.PATH, 'icubam/www/templates'))
    self.popup_template = loader.load('popup.html')

  def to_map_data(self, tree, level):
    nodes = tree.extract_below(level)
    result = []
    for cluster, icus in nodes:
      views = [
        {'name': 'cluster', 'beds': [cluster]},
        {
          'name': 'full',
          'beds': sorted(icus, key=lambda x: x.label)
        },
      ]
      popup = self.popup_template.generate(cluster=cluster, views=views)
      curr = {'popup': popup.decode()}
      curr.update(cluster.as_dict())
      result.append(curr)

    # This sorts the from north to south, so as to avoid overlap on the north.
    result.sort(key=lambda x: x['lat'], reverse=True)
    return result

  def prepare_json(self, user_id=None, center_icu=None, level='dept'):
    # TODO(olivier): all the map ?
    tree = icu_tree.ICUTree()
    for icu in self.db.get_icus():
      tree.add(icu)

    data = self.to_map_data(tree, level)
    anchor = center_icu if center_icu is not None else tree
    center = {'lat': anchor.lat, 'lng': anchor.long}
    return data, center
