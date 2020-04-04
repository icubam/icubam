import dataclasses
import json


class Serizalizable:
  """Base class for message server POSTrequest."""

  def to_json(self):
    return json.dumps(dataclasses.asdict(self))

  def from_json(self, encoded):
    self.__init__(**json.loads(encoded))
