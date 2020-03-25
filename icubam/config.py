"""Manages config variables using .env file."""
from dotenv import load_dotenv
import configparser
import toml
import os
import os.path
import dotmap

INI_PATH = 'icubam.ini'
if not os.path.exists(INI_PATH):
  raise Exception(f"Couldn't find INI file: {INI_PATH}")

config = configparser.ConfigParser()
config.read(INI_PATH)

for var in config['DEFAULT']:
  globals()[var.upper()] = config['DEFAULT'][var]


class Config:

  # All the secret keys
  ENV_KEYS = [
    'SHEET_ID', 'TOKEN_LOC', 'SMS_KEY', 'SECRET_COOKIE', 'JWT_SECRET',
    'GOOGLE_API_KEY']

  def __init__(self, toml_config):
    self.toml_config = toml_config
    if not os.path.exists(toml_config):
      raise Exception(f"Couldn't find INI file: {toml_config}")
    self.conf = dotmap.DotMap(toml.load(self.toml_config))

    self.env = {}
    load_dotenv(verbose=True)
    for key in self.ENV_KEYS:
      self.env[key.upper()] = os.getenv(key)

  def __getattr__(self, key: str):
    if key.upper() == key:
      return self.env.get(key)

    return self.conf.get(key)
