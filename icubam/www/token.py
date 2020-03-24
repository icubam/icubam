from absl import logging
import jwt
from icubam import config


KEY = 'id'


def encode(value) -> str:
  return jwt.encode({KEY: value}, config.JWT_SECRET, algorithm='HS256').decode()


def decode(token: str):
  try:
    obj = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
  except Exception as e:
    logging.error(f"Cannot decode token `{token}`, {e}")
    return
  return obj.get(KEY, None)


def encode_icu(icu_id: int, icu_name: str) -> str:
  return encode({'icu_id': icu_id, 'icu_name': icu_name})
