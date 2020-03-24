"""Manages config variables using .env file."""
import configparser
import os

INI_PATH = '/Users/dulacarnold/Src/icubam/icubam.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

for var in config['DEFAULT']:
  globals()[var.upper()] = config['DEFAULT'][var]
