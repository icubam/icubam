from absl import logging
import functools
import os.path
import json
from typing import List, Optional
import tornado.template

from icubam import icu_tree
from icubam import time_utils
from icubam.db import store


class MapBuilder:
  """Builds the necessary data to build an HTML map."""
  PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

  def __init__(self, config, db, locale):
    self.config = config
    self.db = db
    loader = tornado.template.Loader(
      os.path.join(self.PATH, 'icubam/www/templates')
    )
    self.popup_template = loader.load('popup.html')
    self.locale = locale

  def to_map_data(self, tree, level):
    nodes = tree.extract_below(level)
    result = []
    for cluster, icus in nodes:
      views = [
        {
          'name': 'cluster',
          'beds': [cluster]
        },
        {
          'name': 'full',
          'beds': sorted(icus, key=lambda x: x.label)
        },
      ]

      num_days = self.config.server.num_days_for_stale
      is_stale = functools.partial(
        time_utils.is_stale, days_threshold=num_days
      )
      when = functools.partial(
        time_utils.localewise_time_ago, locale=self.locale
      )
      popup = self.popup_template.generate(
        cluster=cluster, views=views, is_stale=is_stale, when=when
      )
      curr = {'popup': popup.decode()}
      curr.update(cluster.as_dict())
      result.append(curr)

    # This sorts the from north to south, so as to avoid overlap on the north.
    result.sort(key=lambda x: x['lat'], reverse=True)
    return result

  def prepare_jsons(
    self,
    user_id: Optional[int] = None,
    center_icu: Optional[store.ICU] = None,
    regions: Optional[List[int]] = None,
    level: str = 'dept'
  ):
    tree = icu_tree.ICUTree()
    icus = self.db.get_icus()
    if regions:
      icus = [icu for icu in icus if icu.region_id in regions]
    tree.add_many(icus, self.db.get_latest_bed_counts())
    data = self.to_map_data(tree, level)
    anchor = center_icu if center_icu is not None else tree
    center = {'lat': anchor.lat, 'lng': anchor.long}
    return json.dumps(data), json.dumps(center)
