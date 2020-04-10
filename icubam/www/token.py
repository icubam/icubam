from absl import logging
import jwt


class TokenEncoder:
  KEY = 'id'

  def __init__(self, config):
    self.config = config

  def encode(self, value) -> str:
    return jwt.encode({
      self.KEY: value
    },
                      self.config.JWT_SECRET,
                      algorithm='HS256').decode()

  def decode(self, token: str):
    try:
      obj = jwt.decode(token, self.config.JWT_SECRET, algorithms=['HS256'])
    except Exception as e:
      logging.error(f"Cannot decode token `{token}`, {e}")
      return
    return obj.get(self.KEY, None)

  def encode_data(self, user, icu) -> str:
    return self.encode({
      'icu_id': icu.icu_id,
      'icu_name': icu.name,
      'user_id': user.user_id,
      'user_name': user.name
    })
