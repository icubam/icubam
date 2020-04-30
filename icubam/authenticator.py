from absl import logging
import datetime
import numbers
from typing import Optional, Tuple, Union
from icubam.db import store
from icubam.www import token


class Authenticator:
  """Authenticates a user/icu based on available information."""
  def __init__(self, config, db):
    self.config = config
    self.db = db
    self.token_encoder = token.TokenEncoder(self.config)

    # Reads token validation from the config.
    self.validity = self.config.messaging.token_validity_days
    if not isinstance(self.validity, numbers.Number):
      self.validity = None

  def get_or_new_token(
    self,
    user_id: int,
    icu_id: int,
    admin_id: int = None,
    update=False
  ) -> str:
    """Returns the token for a user-icu. May insert it in the database.
    
    If the token is stale, set a new one in the database.
    Args:
     user_id: the user id associated with the token.
     icu_id: the icu id associated with the token.
     admin_id: if set the user id of the admin requesting this token.
     update: if True, may update the token if it is stale in the db.
    """
    token_obj = self.db.get_token_from_ids(user_id, icu_id)

    # This token does not exist, create one.
    if token_obj is None:
      return self.db.add_token(
        admin_id, store.UserICUToken(user_id=user_id, icu_id=icu_id)
      )

    # We do not wish to update stale tokens, return the current one.
    if self.validity is None or not update:
      return token_obj.token

    delta = self.validity + 1
    if token_obj.last_modified is not None:
      time_delta = datetime.datetime.utcnow() - token_obj.last_modified
      delta = time_delta.total_seconds() / 86400

    # The token has expired. Renew it.
    if delta > self.validity:
      return self.db.renew_token(admin_id, user_id, icu_id)

    return token_obj.token

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

  def decode(self, token_str: Union[str, bytes]) -> Optional[Tuple]:
    """Decodes a token using different strategies.
    
    (To cope with backward compatibility.)
    """
    token_str = token_str.decode(
    ) if isinstance(token_str, bytes) else token_str
    if len(token_str) == store.UserICUToken.TOKEN_SIZE:
      user_icu = self.decode_from_db(token_str)
    else:
      logging.info("Decoding an old-fashioned token.")
      user_icu = self.decode_from_jwt(token_str)
    return user_icu

  def decode_from_db(self, token_str: str) -> Optional[Tuple]:
    """Returns a User, ICU trying to get the token from the database."""
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
      logging.warning(f'Token is not a 2-tuple falling back to old token: {e}')
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
