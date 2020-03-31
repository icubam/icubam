from absl import logging
import dataclasses
import json
import tornado.web


@dataclasses.dataclass
class OnOffRequest:
  user_id: int = None
  icu_id: int = None
  on: bool = True
  delay: int = None

  def to_json(self):
    return json.dumps(dataclasses.asdict(self))

  def from_json(self, encoded):
    self.__init__(**json.loads(encoded))


class OnOffHandler(tornado.web.RequestHandler):

  ROUTE = '/onoff'

  def initialize(self, scheduler):
    self.scheduler = scheduler

  def post(self):
    request = OnOffRequest()
    try:
      body = self.request.body
      request.from_json(body.decode())
    except Exception as e:
      self.set_status(400)
      return logging.error(f"Cannot parse request {body}: {e}")

    if request.user_id is None or request.icu_id is None:
      self.set_status(400)
      return logging.error(f"Incomplete request: {body_str}")

    if not request.on:
      self.scheduler.unschedule(request.user_id, request.icu_id)
      return

    user = self.db.get_user(request.user_id)
    if user is None:
      self.set_status(400)
      return logging.error("Unknown user {}".format(user.user_id))

    self.scheduler.schedule(user, request.icu_id)
