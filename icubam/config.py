"""Manages config variables using .env file."""
from dotenv import load_dotenv
import os


load_dotenv(verbose=True)
envs = "SHEET_ID,TOKEN_LOC,SMS_KEY,SMS_ORIG,SECRET_COOKIE,JWT_SECRET,SQLITE_DB"
for env in envs.split(','):
  globals()[env] = os.getenv(env)
