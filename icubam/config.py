"""Manages config variables using .env file."""
from dotenv import load_dotenv
import os
import os.path

ENV_PATH = '.env'
if not os.path.exists(ENV_PATH):
  # !!! Put your path here !!!
  # TODO(oliviert): turn this into a flag
  ENV_PATH = None

load_dotenv(verbose=True, dotenv_path=ENV_PATH)

def get_config_keys(env_path):
  result = []
  with open(env_path, 'r') as fp:
    for line in fp:
      if line.strip().startswith('#'):
        continue

      result.append(line.split('=')[0].strip())
  return result

for env in get_config_keys(ENV_PATH):
  globals()[env] = os.getenv(env)
