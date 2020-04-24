from absl import logging  # noqa: F401
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

    max_size = self.config.server.max_cluster_size
    self.max_cluster_size = max_size if isinstance(max_size, int) else None

    keep_empty = self.config.server.display_empty_icu
    self.keep_empty = keep_empty if isinstance(keep_empty, bool) else False

  def to_map_data(self, tree, level):
    nodes = tree.extract_below(
      level, keep_empty=self.keep_empty, max_nodes=self.max_cluster_size
    )
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
    level: str = 'dept',
  ):
    data = {}
    center = {
      'lat': center_icu.lat,
      'lng': center_icu.long
    } if center_icu else None
    for covid in [True, False]:
      tree = icu_tree.ICUTree(covid=covid)
      icus = self.db.get_icus()
      if regions:
        icus = [icu for icu in icus if icu.region_id in regions]
      tree.add_many(icus, self.db.get_latest_bed_counts())
      data[covid] = self.to_map_data(tree, level)
      if center is None:
        center = {'lat': tree.lat, 'lng': tree.long}

    return json.dumps(data), json.dumps(center)
