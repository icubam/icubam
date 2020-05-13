from absl import logging
import jwt
from typing import Tuple


class TokenEncoder:
  KEY = 'id'

  def __init__(self, config):
    self.config = config

  def encode(self, value) -> str:
    data = {self.KEY: value}
    return jwt.encode(data, self.config.JWT_SECRET, algorithm='HS256').decode()

  def decode(self, token: str):
    try:
      obj = jwt.decode(token, self.config.JWT_SECRET, algorithms=['HS256'])
    except Exception as e:
      logging.error(f"Cannot decode token `{token}`, {e}")
      return
    return obj.get(self.KEY, None)

  def encode_data(self, user, icu) -> str:
    return self.encode((user.user_id, icu.icu_id))

  def authenticate(self, token: str, db) -> Tuple:
    """Returns the user object and the icu object encoded in the token."""
    input_data = self.decode(token)
    if input_data is None:
      logging.warning("No token to be found.")
      return None, None

    try:
      userid, icuid = input_data
    except Exception as e:
      logging.warning(f'Token is not a 2-tuple as expected: {e}')
      userid, icuid = None, None
      if isinstance(input_data, dict):
        userid = input_data.get('user_id', None)
        icuid = input_data.get('icu_id', None)

    user = db.get_user(userid)
    if user is None:
      logging.warning("User does not exist.")
      return None, None

    if user.consent is not None and not user.consent:
      logging.warning("User has bailed out from ICUBAM.")
      return None, None

    user_icu_ids = {i.icu_id: i for i in user.icus}
    icu = user_icu_ids.get(icuid, None)
    if icu is None:
      logging.error("User does not belong the ICU.")
      return None, None

    return user, icu
