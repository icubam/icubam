from icubam.db.store import BedCount, ExternalClient, ICU, User

ALTERATIONS = {
  BedCount: {
    "n_ncovid_free": 3,
    "n_ncovid_occ": 5,
    "n_covid_deaths": 0,
    "n_covid_healed": 0,
    "n_covid_refused": 0,
    "n_covid_transfered": 0,
    "message": "Have a nice day!",
  },
  ICU: {
    "telephone": "33120000000"
  },
  User: {
    "name": "Jean Dumont",
    "email": "jean.dumont@example.org",
    "telephone": "33600000001",
    "password_hash": 42,
  },
  ExternalClient: {
    "name": "Jeanne Externe",
    "email": "jeanne.externe@example.org",
    "telephone": "33600000001",
  },
}


def wipe_db(
  store, keep_beds, reset_admin=False, admin_email=None, admin_pass=None
):
  """
  Wipe sensitive information from a database.

  Parameters
  ----------
  store: icubam store

  keep_beds: bool
      True if bed information should be kept

  reset_admin: bool
      True if admins should be removed and a 'test' admin created.
      If True, require admin_email and admin_pass to be set.

  admin_email: str
      Email of the newly-created admin user (if resetting admins)

  admin_pass: str
      Password of the newly-created admin user (if resetting admins)

  Returns
  -------
  None
  """

  if not keep_beds:
    ALTERATIONS[BedCount].update({"n_covid_free": 2, "n_covid_occ": 4})
  for alteration in ALTERATIONS.items():
    store._session.query(alteration[0]).update(values=alteration[1])

  if reset_admin:
    if None in [admin_email, admin_pass]:
      raise ValueError("admin_email and admin_pass must be defined")
    store._session.query(User).filter(User.is_admin == True
                                      ).update({'is_admin': False})
    hash = store.get_password_hash(admin_pass)
    store.add_user(
      User(name="admin", email=admin_email, password_hash=hash, is_admin=True)
    )
