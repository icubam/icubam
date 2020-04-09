ALTERATIONS = {
  "bed_counts": [
    ("n_ncovid_free", 3),
    ("n_ncovid_occ", 5),
    ("n_covid_deaths", 0),
    ("n_covid_healed", 0),
    ("n_covid_refused", 0),
    ("n_covid_transfered", 0),
    ("message", '"Have a nice day!"'),
  ],
  "icus": [("telephone", "33120000000 + icus.icu_id")
           ],  # we reuse the ID to respect telephone uniqueness constraint
  "users": [
    ("name", '"Jean Dumont"'),
    ("email", '"jean.dumont@example.org"'),
    ("telephone", "33600000001 + users.user_id"),
    ("password_hash", 42),
  ],
  "external_clients": [
    ("name", '"Jean Dumont"'),
    ("email", '"jean.dumont@example.org"'),
    ("telephone", "33600000001 + external_clients.external_client_id"),
  ],
}

def wipe_db(conn, keep_beds):
    """
    Wipe sensitive information from a database.

    Parameters
    ----------
    conn: sqlite3 connection

    keep_beds: bool
        True if bed information should be kept

    Returns
    -------
    None
    """
  cur = conn.cursor()
  if not keep_beds:
    ALTERATIONS["bed_counts"].extend([("n_covid_free", 2), ("n_covid_occ", 4)])
  for alteration in ALTERATIONS.items():
    affectations = ",".join([f"{k} = {v}" for (k, v) in alteration[1]])
    query = f"UPDATE {alteration[0]} SET {affectations};"
    print(query)
    conn.execute(query)
  conn.commit()
  conn.close()


