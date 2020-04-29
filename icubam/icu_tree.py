from icubam.db import store


def get_color(value):
  color = 'red'
  if value < 0.5:
    color = 'green'
  elif value < 0.8:
    color = 'orange'
  return color


class ICUTree:
  """Represents a hierarchical clustering of icus per political region.

  Intermediate nodes contains aggregated counts while the leaves contain
  individual icu information.
  """

  LEVELS = ['country', 'region', 'dept', 'city', 'icu']

  def __init__(self, level='country', covid=True):
    self.id = None
    self.covid = covid
    self.label = None
    self.level = level
    self.phone = None
    self.occ = 0
    self.free = 0
    self.total = 0
    self.death = 0
    self.healed = 0
    self.ratio = 0
    self.lat = 0.0
    self.long = 0.0
    self.color = get_color(self.ratio)
    self.timestamp = None
    self.children = dict()

  def as_dict(self):
    result = {}
    for key in ['id', 'label', 'lat', 'long', 'color', 'free']:
      result[key] = getattr(self, key, None)
    return result

  def get_level_name(self, icu, level=None):
    level = self.level if level is None else level
    region = getattr(icu, level) if hasattr(icu, level) else None
    name = getattr(region, 'name') if hasattr(region, 'name') else region
    return name if name is not None else icu.name

  def get_next_level(self):
    idx = self.LEVELS.index(self.level)
    if idx < len(self.LEVELS) - 1:
      return self.LEVELS[idx + 1]
    return None

  def account_for_beds(self, bedcount):
    occ = bedcount.n_covid_occ if self.covid else bedcount.n_ncovid_occ
    free = bedcount.n_covid_free if self.covid else bedcount.n_ncovid_free
    self.occ += occ if occ is not None else 0
    self.free += free if free is not None else 0
    self.total = self.occ + self.free
    self.ratio = self.occ / self.total if (self.total > 0) else 0
    self.color = get_color(self.ratio)
    if bedcount.n_covid_deaths:
      self.death += bedcount.n_covid_deaths
    if bedcount.n_covid_healed:
      self.healed += bedcount.n_covid_healed
    if bedcount.create_date is not None:
      self.timestamp = 0 if self.timestamp is None else self.timestamp
      self.timestamp = max(self.timestamp, bedcount.create_date.timestamp())

  def set_basic_information(self, icu):
    if self.label is None:
      self.label = self.get_level_name(icu)
      self.id = 'id_{}'.format(self.label.replace(' ', '_'))

    # Set those on last level.
    if self.is_leaf:
      if self.phone is None and icu.telephone is not None:
        self.phone = icu.telephone.lstrip('+')
      if icu.lat is not None:
        self.lat = icu.lat
      if icu.long is not None:
        self.long = icu.long

  def propagate(self, icu, bedcount):
    next_level = self.get_next_level()
    if next_level is None:
      return

    # Recurse
    next_level_name = self.get_level_name(icu, next_level)
    child = self.children.get(
      next_level_name, ICUTree(next_level, covid=self.covid)
    )
    child.add(icu, bedcount)

    # May update position information
    if next_level_name not in self.children:
      self.children[next_level_name] = child
      n = len(self.children)
      if child.lat and child.long:
        self.lat = (child.lat + (n - 1) * self.lat) / n
        self.long = (child.long + (n - 1) * self.long) / n

  def add(self, icu, bedcount):
    if not self.should_add(icu, bedcount):
      return

    bedcount = bedcount if bedcount is not None else store.BedCount()
    self.set_basic_information(icu)
    self.account_for_beds(bedcount)
    self.propagate(icu, bedcount)

  def should_add(self, icu: store.ICU, bedcount: store.BedCount):
    return bedcount is not None and icu.is_active

  def add_many(self, icus, bedcounts):
    bedcounts_index = {b.icu_id: b for b in bedcounts}
    for icu in icus:
      self.add(icu, bedcounts_index.get(icu.icu_id, None))

  @property
  def is_leaf(self):
    return self.level == self.LEVELS[-1]

  def _get_leaves(self, nodes):
    if self.is_leaf:
      nodes.append(self)
    else:
      for child in self.children.values():
        child._get_leaves(nodes)

  def get_leaves(self):
    """Returns all the leaf nodes of the tree."""
    nodes = []
    self._get_leaves(nodes)
    return nodes

  def _extract_below(self, level, nodes, keep_empty=False, max_nodes=None):
    target = self.LEVELS.index(level)
    curr = self.LEVELS.index(self.level)

    recurse = curr < target
    if not recurse:
      leaves = [n for n in self.get_leaves() if (n.total > 0 or keep_empty)]
      if max_nodes is not None and len(leaves) > max_nodes:
        recurse = True
      else:
        nodes.append((self, leaves))

    if recurse:
      for child in self.children.values():
        child._extract_below(
          level, nodes, keep_empty=keep_empty, max_nodes=max_nodes
        )

  def extract_below(self, level, keep_empty=False, max_nodes=10):
    """Returns a list of tuples, where the first element is the cluster info
    and the second one are all the icus in the cluster."""
    nodes = []
    self._extract_below(
      level, nodes, keep_empty=keep_empty, max_nodes=max_nodes
    )
    return nodes
