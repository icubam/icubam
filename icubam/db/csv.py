import csv
import sys

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
    csv_data = csv.reader(open(csv_file_path))

    # check header
    header = next(csv_data, None)
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

    for row in csv_data:
      # insert ICU region if needed
      region = self.store.get_region_by_name(row[header.index("region")])
      if region:
        region_id = region.region_id
      else:
        region_id = self.store.add_region(
          admin_user_id, Region(name=row[header.index("region")])
        )

      # insert ICU if needed
      icu = self.store.get_icu_by_name(row[header.index("icu_name")])
      icu_info = {
        "name": row[header.index("icu_name")],
        "region_id": region_id,
        "dept": row[header.index("dept")],
        "city": row[header.index("city")],
        "lat": row[header.index("lat")],
        "long": row[header.index("long")],
        "telephone": row[header.index("telephone")],
      }
      if icu:
        # update ICU
        if forceUpdate:
          icu_id = icu.icu_id
          self.store.update_icu(admin_user_id, icu_id, icu_info)
          print(
            "IMPORT CSV : overwrite ICU " + row[header.index("icu_name")] +
            " --forceUpdate"
          )
        else:
          print(
            "IMPORT CSV : skip ICU " + row[header.index("icu_name")] +
            " already exist in db (use --forceUpdate to update anyway)"
          )
      else:
        # create ICU
        icu_id = self.store.add_icu(admin_user_id, ICU(**icu_info))
        print("IMPORT CSV : create ICU " + row[header.index("icu_name")])

  def import_users(
    self, admin_user_id: int, csv_file_path: str, forceUpdate=False
  ):
    csv_data = csv.reader(open(csv_file_path))

    # check header
    header = next(csv_data, None)
    expected_column = ['icu_name', 'name', 'tel', 'description']
    for c in expected_column:
      if c not in header:
        print(
          "IMPORT CSV : ERROR : invalid USER file, missing column " + c +
          " in header"
        )
        sys.exit(0)

    for row in csv_data:
      icu = self.store.get_icu_by_name(row[header.index("icu_name")])
      if icu is None:
        print(
          "IMPORT CSV : skip USER " + row[header.index("name")] +
          ", no existing ICU named " + row[header.index("icu_name")] +
          ". you should import/create this ICU first"
        )
      else:
        user = self.store.get_user_by_phone(row[header.index("tel")])
        user_info = {
          "name": row[header.index("name")],
          "telephone": row[header.index("tel")],
          "description": row[header.index("description")],
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
              "IMPORT CSV : overwrite USER " + row[header.index("name")] +
              " --forceUpdate"
            )
          else:
            print(
              "IMPORT CSV : skip USER " + row[header.index("name")] +
              " already exist in db (use --forceUpdate to update anyway)"
            )
        else:
          # create USER
          self.store.add_user_to_icu(
            admin_user_id, icu.icu_id, User(**user_info)
          )
          print("IMPORT CSV : create ICU " + row[header.index("name")])

  def export_icus(self, csv_file_path: str):

    with open(csv_file_path, 'w') as csvfile:
      header = [
        "icu_name", "region", "dept", "city", "lat", "long", "telephone"
      ]
      writer = csv.DictWriter(csvfile, fieldnames=header)
      writer.writeheader()

      for icu in self.store.get_icus():
        region_name = self.store.get_region(icu.region_id).name
        writer.writerow({
          "icu_name": icu.name,
          "region": region_name,
          "dept": icu.dept,
          "city": icu.city,
          "lat": icu.lat,
          "long": icu.long,
          "telephone": icu.telephone
        })

  def export_users(self, csv_file_path: str):

    with open(csv_file_path, 'w') as csvfile:
      header = ["icu_name", "name", "tel", "description"]
      writer = csv.DictWriter(csvfile, fieldnames=header)
      writer.writeheader()

      for user in self.store.get_users():
        for icu in user.icus:
          writer.writerow({
            "icu_name": icu.name,
            "name": user.name,
            "tel": user.telephone,
            "description": user.description
          })
