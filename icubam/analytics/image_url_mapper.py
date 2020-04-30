from typing import Optional, List


class ImageURLMapper:
  """Maps plot image query to a URL so it can be loaded via static ressources"""
  def __init__(self, filenames: Optional[List[str]] = None):
    if filenames is not None:
      self.filenames = filenames
    else:
      self.filenames = []

  @staticmethod
  def make_path(
    plot_name,
    region_id: Optional[int] = None,
    region: Optional[str] = None,
    extension: Optional[str] = None
  ) -> str:
    """Map a query to a file path"""
    tokens = []
    if region_id is None:
      tokens.append('National')
    elif region is None:
      raise ValueError('when region_id is not None, region must be provided!')
    else:
      tokens.append(f'region_id={region_id:.0f}-{region}')

    tokens.append(plot_name)
    path = '-'.join(tokens)
    if extension is not None:
      path += ('.' + extension.strip('.'))
    return path
