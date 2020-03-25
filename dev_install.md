# Developer install 

## Installing

This explains how to run a local instance of `icubam` on a developer's machine. We use conda, but you might choose virtualenv.

Steps:

- create a conda environment (e.g. `conda create -n icubam python=3.8`)
- activate the environment (`conda activate icubam`)
- install deps with `pip install -r requirements.txt`
- install the package in edit mode by running `pip install -e .`

** Note: ** in addition to the python dependencies described in `requirements.txt`, `icubam` requires SQLite >= 3.24.0 as it uses upsert statements.

### Configuration

Create a `icubam.ini` file at root of the project containing the following keys:
```
[DEFAULT]
SHEET_ID=
TOKEN_LOC=
SMS_KEY =
SMS_ORIG=
SECRET_COOKIE=
JWT_SECRET=
SQLITE_DB=
GOOGLE_API_KEY=
```

### Pre-populate DB with test data

Create a fake database in order to be able to play with it:
`python scripts/populate_db_fake.py`

The databse will be named `test.db`.
Please, rename this file and/or modify the `icubam.ini` file for `SQLITE_DB` to point on this file.

## Running locally

Start the server locally:
`python scripts/run_server.py`

Will produce the following logs:
```
I0324 19:02:15.784908 139983874058048 server.py:32] UpdateHandler serving on /update
I0324 19:02:15.785018 139983874058048 server.py:32] HomeHandler serving on /
I0324 19:02:15.785090 139983874058048 server.py:49] Running WWWServer on port 8888
I0324 19:02:15.788751 139983874058048 server.py:51] http://localhost:8888/update?id=<A_VERY_LONG_ID>
```

Follow the proposed link `http://localhost:8888/update?id=<A_VERY_LONG_ID>`

## Running unit tests

The unit tests require `TOKEN_LOC` to be set with a valid `token.pickle` file in `icubam.ini` file.

To start the tests, run `python -m unittest`
