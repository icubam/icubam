"""Google sheets storage backend wrapper."""
import pickle
import logging
import pandas as pd
from googleapiclient.discovery import build


class SheetsDB:
  """Wrap a google sheet and serve up DataFrames from it."""
  def __init__(self, token_loc, sheet_id):
    """Given a token file and a sheet id, loads the sheet to be queried."""
    self._token_loc = token_loc
    self._sheet_id = sheet_id

    with open(self._token_loc, "rb") as token:
      self._creds = pickle.load(token)

    logging.info(
      f"Successfully loaded token from {self._token_loc} "
      "for sheet {sheet_id}."
    )

    self.service = build(
      "sheets", "v4", credentials=self._creds, cache_discovery=False
    )
    self.sheet = self.service.spreadsheets()

  def get_sheet_as_pd(self, sheet_name):
    """Returns a pandas DF of bed counts."""
    result = (
      self.sheet.values().get(spreadsheetId=self._sheet_id,
                              range=sheet_name).execute()
    )
    values = result.get("values", [])

    columns = values[0]
    data = values[1:]
    data_df = pd.DataFrame(data, columns=columns)
    return data_df

  def get_users(self):
    """Returns a pandas DF of bed counts."""
    return self.get_sheet_as_pd("Users")

  def get_icus(self):
    """Returns a pandas DF of bed counts."""
    return self.get_sheet_as_pd("ICUs")
