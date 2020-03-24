"""Manages config variables using .env file."""
from dotenv import load_dotenv
import os

ENV_PATH =
load_dotenv(verbose=True, dotenv_path=ENV_PATH)
envs = ("SHEET_ID,TOKEN_LOC,SMS_KEY,SMS_ORIG,SECRET_COOKIE,JWT_SECRET,"
        "SQLITE_DB,GOOGLE_API_KEY")
for env in envs.split(','):
  globals()[env] = os.getenv(env)
