import io
import tornado.httpclient

from icubam.analytics import dataset, client


class MockClient(client.AnalyticsClient):
  def __init__(self, config, db):
    super().__init__(config)
    self.dataset = dataset.Dataset(db)

  async def get(self, collection: str, query: str):
    df = self.dataset.get(collection)
    body = df.to_csv(index=False) if 'csv' in query else df.to_html()
    buf = io.BytesIO()
    buf.write(body.encode())
    return tornado.httpclient.HTTPResponse(
      tornado.httpclient.HTTPRequest('collection', method='get'),
      buffer=buf,
      code=200,
    )
