import sys
import pandas as pd

from icubam.db.store import Store, StoreFactory, BedCount, ExternalClient, ICU, Region, User


class CSV:
  """ """
  def __init__(self, db):
    self.store = db

  def get_default_admin(self):
    # create default admin
    return self.store.add_default_admin()

  def import_icus(
    self, admin_user_id: int, csv_file_path: str, forceUpdate=False
  ):
    csv_data = pd.read_csv(csv_file_path)

    # check header
    header = csv_data.columns
    expected_column = [
      'icu_name', 'region', 'dept', 'city', 'lat', 'long', 'telephone'
    ]
    for c in expected_column:
      if c not in header:
        print(
          "IMPORT CSV : ERROR : invalid ICU file, missing column " + c +
          " in header"
        )
        sys.exit(0)

    for index, row in csv_data.iterrows():
      # insert ICU region if needed
      region = self.store.get_region_by_name(row["region"])
      if region:
        region_id = region.region_id
      else:
        region_id = self.store.add_region(
          admin_user_id, Region(name=row["region"])
        )

      # insert ICU if needed
      icu = self.store.get_icu_by_name(row["icu_name"])
      icu_info = {
        "name": row["icu_name"],
        "region_id": region_id,
        "dept": row["dept"],
        "city": row["city"],
        "lat": row["lat"],
        "long": row["long"],
        "telephone": row["telephone"],
      }
      if icu:
        # update ICU
        if forceUpdate:
          icu_id = icu.icu_id
          self.store.update_icu(admin_user_id, icu_id, icu_info)
          print(
            "IMPORT CSV : overwrite ICU " + row["icu_name"] + " --forceUpdate"
          )
        else:
          print(
            "IMPORT CSV : skip ICU " + row["icu_name"] +
            " already exist in db (use --forceUpdate to update anyway)"
          )
      else:
        # create ICU
        icu_id = self.store.add_icu(admin_user_id, ICU(**icu_info))
        print("IMPORT CSV : create ICU " + row["icu_name"])

  def import_users(
    self, admin_user_id: int, csv_file_path: str, forceUpdate=False
  ):
    csv_data = pd.read_csv(csv_file_path)

    # check header
    header = csv_data.columns
    expected_column = ['icu_name', 'name', 'tel', 'description']
    for c in expected_column:
      if c not in header:
        print(
          "IMPORT CSV : ERROR : invalid USER file, missing column " + c +
          " in header"
        )
        sys.exit(0)

    for index, row in csv_data.iterrows():
      icu = self.store.get_icu_by_name(row["icu_name"])
      if icu is None:
        print(
          "IMPORT CSV : skip USER " + row["name"] +
          ", no existing ICU named " + row["icu_name"] +
          ". you should import/create this ICU first"
        )
      else:
        user = self.store.get_user_by_phone(row["tel"])
        user_info = {
          "name": row["name"],
          "telephone": row["tel"],
          "description": row["description"],
          "email": "a@bc.org",
          "is_active": True,
          "is_admin": False,
        }

        if user:
          # update USER
          if (not self.store.can_edit_bed_count(user.user_id, icu.icu_id)):
            self.store.assign_user_to_icu(
              admin_user_id, user.user_id, icu.icu_id
            )
          if forceUpdate:
            self.store.update_user(admin_user_id, user.user_id, user_info)
            print(
              "IMPORT CSV : overwrite USER " + row["name"] + " --forceUpdate"
            )
          else:
            print(
              "IMPORT CSV : skip USER " + row["name"] +
              " already exist in db (use --forceUpdate to update anyway)"
            )
        else:
          # create USER
          self.store.add_user_to_icu(
            admin_user_id, icu.icu_id, User(**user_info)
          )
          print("IMPORT CSV : create ICU " + row["name"])

  def export_icus(self, csv_file_path: str):
    header = ["icu_name", "region", "dept", "city", "lat", "long", "telephone"]
    df = pd.DataFrame(columns=header)

    for icu in self.store.get_icus():
      region_name = self.store.get_region(icu.region_id).name
      df = df.append({
        "icu_name": icu.name,
        "region": region_name,
        "dept": icu.dept,
        "city": icu.city,
        "lat": icu.lat,
        "long": icu.long,
        "telephone": icu.telephone
      },
                     ignore_index=True)
    df.to_csv(csv_file_path, index=False, line_terminator="\r\n")

  def export_users(self, csv_file_path: str):
    header = ["icu_name", "name", "tel", "description"]
    df = pd.DataFrame(columns=header)

    for user in self.store.get_users():
      for icu in user.icus:
        df = df.append({
          "icu_name": icu.name,
          "name": user.name,
          "tel": user.telephone,
          "description": user.description
        },
                       ignore_index=True)
    df.to_csv(csv_file_path, index=False, line_terminator="\r\n")
