import os.path
import tornado.httpclient
from icubam.analytics.handlers import dataset


class AnalyticsClient:
  """Client for HTTP-based comnunication with the MessageServer"""
  def __init__(self, config):
    self.config = config
    self.http_client = tornado.httpclient.AsyncHTTPClient()

  async def get(self, collection: str, query: str):
    path = os.path.join(
      self.config.analytics.base_url, dataset.DatasetHandler.ROUTE.lstrip('/')
    )
    url = f'{path}?{query}'
    return await self.http_client.fetch(
      tornado.httpclient.HTTPRequest(
        url, method='GET', request_timeout=self.config.analytics.timeout
      )
    )
