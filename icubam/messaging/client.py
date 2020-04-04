from absl import logging
import json
import os.path
from tornado import httpclient
from typing import List, Optional

from icubam.messaging.handlers import onoff, schedule


class MessageServerClient:
  """Client for HTTP-based comnunication with the MessageServer"""

  def __init__(self, config):
    self.config = config
    self.http_client = httpclient.AsyncHTTPClient()

  async def fetch(self, handler, request):
    url = os.path.join(
        self.config.messaging.base_url, handler.ROUTE.lstrip('/'))
    return await self.http_client.fetch(httpclient.HTTPRequest(
        url, body=request.to_json(), method='POST',
        request_timeout=self.config.messaging.timeout))

  async def notify(self,
                   user_id: int,
                   icu_ids: List[int],
                   on: bool = True,
                   delay: Optional[int] = None):
    """Notify the scheduler that a user must be added / remove from the loop."""
    if not icu_ids:
      return logging.info('nothing to change. Aborting')

    request = onoff.OnOffRequest(user_id, list(icu_ids), on, delay)
    return await self.fetch(onoff.OnOffHandler, request)

  async def get_scheduled_messages(self, user_id):
    request = schedule.ScheduleRequest(user_id)
    response = await self.fetch(schedule.ScheduleHandler, request)
    if response.code != 200:
      logging.error('Something went wrong while fetching messages')
      return []

    try:
      result = json.loads(response.body.decode())
    except Exception as e:
      logging.error(f"Could not parse {response.body} as ScheduleResponse: {e}")
      return []

    return result
