from absl import logging
from typing import Optional, Tuple
from icubam.db import store
from icubam.www import token


class Authenticator:
  """Authenticates a user/icu based on available information."""
  def __init__(self, config, db):
    self.config = config
    self.db = db
    self.token_encoder = token.TokenEncoder(self.config)

  def authenticate(self, token_str: str) -> Optional[Tuple]:
    """Decodes the token and check that the data is valid."""
    user_icu = self.decode(token_str)
    if user_icu is None:
      logging.warning(f"Cannot authenticate {token_str}")
      return None
    user, icu = user_icu

    if user.consent is not None and not user.consent:
      logging.warning(f"User has bailed out from ICUBAM.")
      return None

    if not user.is_active or not icu.is_active:
      logging.warning("User/ICU is not active.")
      return None

    if icu.icu_id not in {i.icu_id: i for i in user.icus}:
      logging.warning(f"User {user.user_id} does not belong ICU {icu.icu_id}.")
      return None

    return user, icu

  def decode(self, token_str: str) -> Optional[Tuple]:
    """Decodes a token using different strategies.
    
    (To cope with backward compatibility.)
    """
    user_icu = self.decode_from_db(token_str)
    if user_icu is None:
      user_icu = self.decode_from_jwt(token_str)
    return user_icu

  def decode_from_db(self, token_str: str) -> Optional[Tuple]:
    """Returns a User, ICU trying to get the token from the database."""
    if len(token_str) != store.UserICUToken.TOKEN_SIZE:
      return None

    uit = self.db.get_token(token_str)
    if uit is None:
      logging.warning(f'No token {token_str}')
      return None

    return uit.user, uit.icu

  def decode_from_jwt(self, token_str: str) -> Optional[Tuple]:
    """Returns a User, ICU trying read a jwt."""
    data = self.token_encoder.decode(token_str)
    if data is None:
      logging.warning("No token to be found.")
      return None

    try:
      userid, icuid = data
    except Exception as e:
      logging.error(f'Token is not a 2-tuple falling back to old token: {e}')
      userid, icuid = None, None
      if isinstance(data, dict):
        userid = data.get('user_id', None)
        icuid = data.get('icu_id', None)

    user = self.db.get_user(userid)
    if user is None:
      logging.warning(f"User {userid} does not exist.")
      return None

    icu = self.db.get_icu(icuid)
    if icu is None:
      logging.warning(f"ICU {icuid} does not exist.")
      return None

    return user, icu
