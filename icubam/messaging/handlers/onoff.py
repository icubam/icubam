from typing import Optional

from absl import logging
import dataclasses
import json
import tornado.web
from typing import List

from icubam.messaging import serializable


@dataclasses.dataclass
class OnOffRequest(serializable.Serizalizable):
  user_id: Optional[int] = None
  icu_ids: Optional[List[int]] = None
  on: bool = True
  delay: Optional[int] = None


class OnOffHandler(tornado.web.RequestHandler):
  """This handler is used to activate of deactivate the reception of messages.

  Two tests cases are when a new user is created, the message server should be
  informed so that she starts receving messages, and when a user opt-out, she
  should be removed from there.
  """

  ROUTE = '/onoff'

  def initialize(self, db_factory, scheduler):
    self.db = db_factory.create()
    self.scheduler = scheduler

  async def post(self):
    request = OnOffRequest()
    try:
      body = self.request.body
      request.from_json(body.decode())
    except Exception as e:
      self.set_status(400)
      return logging.error(f"Cannot parse request {body}: {e}")

    if request.user_id is None or request.icu_ids is None:
      self.set_status(400)
      return logging.error(f"Incomplete request: {body_str}")

    if not request.on:
      for icu_id in request.icu_ids:
        self.scheduler.unschedule(request.user_id, icu_id)
      return

    user = self.db.get_user(request.user_id)
    if user is None:
      self.set_status(400)
      return logging.error("Unknown user {}".format(user.user_id))

    user_icus = {i.icu_id: i for i in user.icus}
    for icu_id in request.icu_ids:
      icu = user_icus.get(icu_id, None)
      if icu is None:
        logging.error(
          f"User {user.user_id} does not belong to ICU {icu.icu_id}"
        )
        continue
      self.scheduler.schedule(user, icu, request.delay)
