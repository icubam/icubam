from tornado import httpclient
from icubam.messaging.handlers.onoff import OnOffHandler, OnOffRequest

"""Client for HTTP-based comnunication with the MessageServer"""
class MessageServerClient(object):
  def __init__(self, config):
    self.http_client = httpclient.AsyncHTTPClient()
    self.base_url = config.messaging.base_url
    self.url = "{0}/{1}".format(self.base_url.strip("/"), OnOffHandler.ROUTE)

  # TODO(olivier): make OnOffHandler receive a list of ICU ids so we can do
  # everything in one HTTP request. This won't change the interface for the
  # clients though.
  def _request(self, user_id, icu_ids, activate: bool):
    onoff_req = OnOffRequest()
    onoff_req.user_id = user_id
    onoff_req.onoff = activate
    for icu_id in icu_ids:
      onoff_req.icu_id = icu_id
      onoff_req.on = activate
      body = onoff_req.to_json()
      request = httpclient.HTTPRequest(url, body=body, method="POST")
      self.http_client.fetch(request)

  def notify(self, user_id, icu_ids, onoff):
    return self._request(user_id, icu_ids, activate=onoff)
