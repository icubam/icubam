"""Manages config variables using .env file."""

import logging
import os.path
from dotenv import load_dotenv

import dotmap
import toml

DEFAULT_DOTENV_PATH = "resources/icubam.env"
DEFAULT_CONFIG_PATH = "resources/config.toml"


class Config:
  """A class to read the configuration both from .env and from a toml file.

  Upper keys are for the .env secrets and lower keys for the toml file.
  """

  # All the secret keys
  ENV_KEYS = [
    'SMS_KEY', 'SECRET_COOKIE', 'JWT_SECRET', 'GOOGLE_API_KEY', 'MB_KEY',
    'NX_KEY', 'NX_API', 'TW_KEY', 'TW_API', 'DB_SALT', 'SMTP_HOST',
    'SMTP_USER', 'SMTP_PASSWORD', 'EMAIL_FROM', 'SENTRY_URL', 'SENTRY_ENV'
  ]

  def __init__(self, toml_config, env_path=None):
    """If env_path is None, it will try to find it by itself."""
    self.toml_config = toml_config
    if not os.path.exists(toml_config):
      raise Exception(f"Couldn't find INI file: {toml_config}")
    sub_conf = self._preprocess(toml.load(self.toml_config))
    self.conf = dotmap.DotMap(sub_conf)

    self.env = {}
    load_dotenv(verbose=True, dotenv_path=env_path)
    logging.info(f"Loading env vars from: {env_path}.")
    for key in self.ENV_KEYS:
      self.env[key.upper()] = os.getenv(key)
    logging.info(f"Loaded: {self.env}.")

  def _preprocess(self, conf):
    """Recursively enforce lower keys."""
    result = {}
    for k, v in conf.items():
      if not isinstance(v, dict):
        result[k.lower()] = v
      else:
        result[k.lower()] = self._preprocess(v)
    return result

  def __getitem__(self, key: str):
    if key.upper() == key:
      return self.env.get(key)
    if self.conf.has_key(key):
      # TODO: We need to handle when attribute lookups fail
      # on the returned object, which currently returns a DotMat
      # object, however that's up to the dotmap library.
      return self.conf.get(key)
    raise KeyError(f"key '{key}' does not exist!")

  def __getattr__(self, key: str):
    raise_err = False
    try:
      res = self[key]
    except KeyError:
      raise_err = True
    # Avoid raising an exception inside an exception for traceback
    # readability.
    if raise_err:
      raise AttributeError(f"attribute '{key}' does not exist!")
    return res

  def __setstate__(self, state):
    self.__dict__ = state

  def __getstate__(self):
    return self.__dict__
