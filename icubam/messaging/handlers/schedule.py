from absl import logging
import dataclasses
import json
import tornado.web
from typing import List, Tuple, Optional

from icubam.messaging import message
from icubam.messaging import serializable


@dataclasses.dataclass
class ScheduleRequest(serializable.Serizalizable):
  user_id: Optional[int] = None


@dataclasses.dataclass
class ScheduledMessage:
  icu_id: Optional[int] = None
  user_id: Optional[int] = None
  user_name: Optional[str] = None
  icu_name: Optional[str] = None
  phone: Optional[str] = None
  attempts: Optional[int] = 0
  first_sent: Optional[int] = None
  when: Optional[int] = None
  url: Optional[str] = None


class ScheduleHandler(tornado.web.RequestHandler):
  """This handler returns all the scheduled messages information."""

  ROUTE = '/schedule'

  def initialize(self, db_factory, scheduler):
    self.db = db_factory.create()
    self.scheduler = scheduler

  def build_response(self, messages: List[Tuple[message.Message, int]]):
    response = []
    for msg, when in messages:
      curr = ScheduledMessage(
        msg.icu_id, msg.user_id, msg.user_name, msg.icu_name, msg.phone,
        msg.attempts, msg.first_sent, when, msg.url
      )
      response.append(dataclasses.asdict(curr))
    return response

  async def post(self):
    request = ScheduleRequest()
    try:
      body_str = self.request.body.decode()
      request.from_json(body_str)
    except Exception as e:
      self.set_status(400)
      return logging.error(f"Cannot parse request {self.request.body}: {e}")

    if request.user_id is None:
      self.set_status(400)
      return logging.error(f"Incomplete request: {body_str}")

    user = self.db.get_user(request.user_id)
    if user is None:
      logging.error(f"No such user {request.user_id}")
      return

    icu_ids = [icu.icu_id for icu in self.db.get_managed_icus(user.user_id)]
    messages = self.scheduler.get_messages(icu_ids)
    response = self.build_response(messages)
    return self.write(json.dumps(response))
