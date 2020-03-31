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
  """This handler is used to activate of deactivate the reception of messages.

  Two tests cases are when a new user is created, the message server should be
  informed so that she starts receving messages, and when a user opt-out, she
  should be removed from there.
  """

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

    icu = {i.icu_id: icu for i in user.icus}.get(request.icu_id, None)
    if icu is None:
      self.set_status(400)
      return logging.error("User {} does not belong to ICU {}".format(
        user.user_id, request.icu_id))

    self.scheduler.schedule(user, icu, request.delay)
