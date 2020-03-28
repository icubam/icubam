# Developer install 

## Installing

This explains how to run a local instance of `icubam` on a developer's machine. We use conda to setup a virtual 
environment and install the required packages. Conda/miniconda [installation](https://docs.conda.io/en/latest/miniconda.html).

Steps:

- create a conda environment and install the packages (e.g. `conda env create -f environment.yml`)
- activate the environment (`conda activate icubam`)
- install the package in edit mode by running `conda develop .`

**Note:** in addition to the python dependencies described in `environment.yml`, `icubam` requires SQLite >= 3.24.0 as it uses upsert statements.

### Configuration

Create a `.env` file at root of the project containing the following keys:
```
SHEET_ID=
TOKEN_LOC=
SMS_KEY=
SECRET_COOKIE=
JWT_SECRET=
GOOGLE_API_KEY=
MB_KEY= 
NX_KEY= 
NX_API= 
TW_KEY=
TW_API=
```

### Pre-populate DB with test data

Create a fake database in order to be able to play with it:
`python scripts/populate_db_fake.py`

The databse will be named `icubam.db`.

If required, change the DB path property in the default `resources/config.toml` file, or update the provided toml 
configuration file.

## Running locally

Start the server locally:
`python scripts/run_server.py`

Note: by default, the server uses the config toml file `resources/config.toml` and the environment variables in `.env`.
Alternative files can be used by providing the command line parameters `--config=...` and/or `--dotenv_path=...`

Will produce the following logs:
```
I0324 19:02:15.784908 139983874058048 server.py:32] UpdateHandler serving on /update
I0324 19:02:15.785018 139983874058048 server.py:32] HomeHandler serving on /
I0324 19:02:15.785090 139983874058048 server.py:49] Running WWWServer on port 8888
I0324 19:02:15.788751 139983874058048 server.py:51] http://localhost:8888/update?id=<A_VERY_LONG_ID>
```

Follow the proposed link above to activate the web app `http://localhost:8888/update?id=<A_VERY_LONG_ID>`

## Running unit tests

The unit tests require `TOKEN_LOC` to be set with a valid `token.pickle` file in the `.env` file.

To start the tests, install `pytest` and run `pytest`

## Docker install

First, install Docker on your host (check official [documentation](https://docs.docker.com/)).

To build the ICUBAM Docker image (providing the config file archive, the image version number and the target 
configuration)
    
```
./docker_build deploy_configs.tgz 1.0 dev
```
    
To launch the container (providing the host's port to map the tornado server's defaut port 8888)

```
./docker_run icubam:1.0 9000
``` 

To activate the server, use `docker logs CONTIANER_ID` to retrevie the URL and open the URL. Replace the port after 
localhost with the public port chosen for the container (9000 in the example above).  