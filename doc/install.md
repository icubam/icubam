# Developer install

## Installing

This explains how to run a local instance of `icubam` on a developer's machine. We use conda, but you might choose virtualenv.

Steps:

- create a conda environment (e.g. `conda create -n icubam python=3.8`)
- activate the environment (`conda activate icubam`)
- install deps with `pip install -r requirements.txt`
- install the package in edit mode by running `pip install -e .`

**Note:** in addition to the python dependencies described in `requirements.txt`, `icubam` requires SQLite >= 3.24.0 as it uses upsert statements.

### Configuration

Create a `resources/icubam.env` file containing the following keys:
```
SECRET_COOKIE=random_secret
JWT_SECRET=another_secret
GOOGLE_API_KEY=a google maps api key
TW_KEY=
TW_API=
DB_SALT=
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
```

N.B.: You can name and move this file as you want but you will have to add
`--dotenv_path=path/to/my_icubam.env` to the scripts when launching them.

### Pre-populate DB with test data

Create a fake database in order to be able to play with it:
`python scripts/populate_db_fake.py --config=resources/config.toml --mode=dev`

The database will be named `test.db`, cf. `resources/config.toml`.

## Running unit tests

A few unit tests require `TOKEN_LOC` to be set with a valid `token.pickle` file in the `resources/icubam.env` file. If the TOKEN_LOC variable is not present, those tests will be skipped.

To start the tests, install `pytest` and run `pytest`

## Running locally


### Main server

Start the main server locally:
`python scripts/run_server.py --config=resources/config.toml --mode=dev`

Will produce the following logs:
```
I0324 19:02:15.784908 139983874058048 server.py:32] UpdateHandler serving on /update
I0324 19:02:15.785018 139983874058048 server.py:32] HomeHandler serving on /
I0324 19:02:15.785090 139983874058048 server.py:49] Running WWWServer on port 8888
I0324 19:02:15.788751 139983874058048 server.py:51] http://localhost:8888/update?id=<A_VERY_LONG_ID>
```

Follow the proposed link `http://localhost:8888/update?id=<A_VERY_LONG_ID>`

### Backoffice server

Start the backoffice server locally,
```
python scripts/run_server.py --server=backoffice
```

Then open backoffice at [http://localhost:8890](http://localhost:8890) and
login with user credentials created by the `populate_db_fake.py` script,
 - user: `admin@test.org`
 - password: `password`

## Docker

To build and run the application using Docker (docker or docker-compose) check the [documentation](./docker/README.md)
in the docker folder.

## Source code formatting

The codebase is formatted using `yapf`. 

Running `yapf -i <filename>` will reformat a file in-place. Running `yapf -i -r .` at the root of the working copy will reformat the whole project in-place.

For convenience, there is a pre-commit hook available that will reject non-yapfing code. This requires an initial setup step:

- Install the development requirements using `pip install -r requirements-dev.txt` (this will pull yapf and pre-commit)
- Run `pre-commit install` to set up the git hook. (this only needs to be done once)
