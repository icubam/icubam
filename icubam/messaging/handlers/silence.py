import json
import dataclasses
from absl import logging
from icubam.www.handlers import base


@dataclasses.dataclass
class SilenceRequest:
  user_id: int = None

  def to_json(self):
    return json.dumps(dataclasses.asdict(self))

  def from_json(self, encoded):
    self.__init__(**json.loads(encoded))


class SilenceHandler(base.BaseHandler):

  ROUTE = '/update'

  def initialize(self, config, db, scheduler):
    super().initialize(config, db)
    self.scheduler = scheduler

  def post(self):
    try:
      body_str = self.request.body.decode()
      data = json.loads(body_str)
    except Exception as e:
      self.set_status(400)
      return logging.error(f"Cannot parse request {body_str}: {e}")

    user_id = data.get('user_id', None)
    if user_id is None:
      self.set_status(400)
      return logging.error(f"Missing user id in request {body_str}")

    self.scheduler.unschedule(user_id)
