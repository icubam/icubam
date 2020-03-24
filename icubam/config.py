"""Manages config variables using .env file."""
import configparser
import os.path

INI_PATH = '/Users/dulacarnold/Src/icubam/icubam.ini'
if not os.path.exists(INI_PATH):
  raise Exception(f"Couldn't find INI file: {INI_PATH}")

config = configparser.ConfigParser()
config.read(INI_PATH)

for var in config['DEFAULT']:
  globals()[var.upper()] = config['DEFAULT'][var]
