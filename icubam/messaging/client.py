from absl import logging
import os.path
from tornado import httpclient
from typing import List, Optional

from icubam.messaging.handlers import onoff


class MessageServerClient:
  """Client for HTTP-based comnunication with the MessageServer"""

  def __init__(self, config):
    self.config = config
    self.http_client = httpclient.AsyncHTTPClient()

  async def notify(self,
                   user_id: int,
                   icu_ids: List[int],
                   on: bool = True,
                   delay: Optional[int] = None):
    """Notify the scheduler that a user must be added / remove from the loop."""
    if not icu_ids:
      return logging.info('nothing to change. Aborting')

    request = onoff.OnOffRequest(user_id, list(icu_ids), on, delay)
    url = os.path.join(self.config.messaging.base_url,
                       onoff.OnOffHandler.ROUTE.lstrip('/'))
    return await self.http_client.fetch(
      httpclient.HTTPRequest(url, body=request.to_json(), method='POST'))
