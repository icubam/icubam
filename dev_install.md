# Developer install 

## Installing

This explains how to run a local instance of `icubam` on a developer's machine. We use conda to setup a virtual 
environment and install the required packages with pip. 
We use conda ([installation](https://docs.conda.io/en/latest/miniconda.html)), but you might choose virtualenv.

Steps:

- create a conda environment (e.g. `conda create -n icubam python=3.8`)
- activate the environment (`conda activate icubam`)
- install deps with `pip install -r requirements.txt`
- install the package in edit mode by running `pip install -e .`

**Note:** in addition to the python dependencies described in `requirements.txt`, `icubam` requires SQLite >= 3.24.0 as it uses upsert statements.

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

The databse will be named `icubam.db` and is generated in the current folder.

If required, change the DB path property in the default `resources/config.toml` file, or update the provided toml 
configuration file.

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

Follow the proposed link above to activate the web app `http://localhost:8888/update?id=<A_VERY_LONG_ID>`

Note: by default, the server uses the config toml file `resources/config.toml` and the environment variables in `.env`.
Alternative files can be used by providing the command line parameters `--config=...` and/or `--dotenv_path=...`

For example
```
python3 scripts/run_server.py --port 8888 --dotenv_path=/home/icubam/resources/icubam.env --config=/home/icubam/resources/icubam.toml
```

## Running unit tests

The unit tests require `TOKEN_LOC` to be set with a valid `token.pickle` file in the `.env` file.

To start the tests, install `pytest` and run `pytest`

## Docker install

First, install Docker on your host (check official [documentation](https://docs.docker.com/)).

To build the ICUBAM Docker image, just provide the image version number.
    
```
./docker_build.sh 1.0 
```
    
To launch the container, provide the image to use, the target port and the targeted environment (dev, prod)
 
Notes:
- the script assumes the tornado server is launched on port 8888)
- the script assumes that the required configuration files are proprerly installed
  
```
./docker_run.sh icubam:1.0 9000 dev
``` 
The command will display the long version of the container ID and exit after a few seconds. The xcontainer ID and 
status can be retrieved with the command
```
docker ps
```

To activate the server, use `docker logs CONTAINER_ID` to retrieve the URL and open the URL. Replace the port after 
localhost with the public port chosen for the container (9000 in the example above).  

## Docker compose

To launch the complete install (server, sms server, nginx, certbot containers), use the docker-compose command

Note:
- the proper nginx configuration file should be setup in `configs/nginx`
- the proper environment should be set in the `docker-compose.yml` file
- the icubam configuration files (database, toml, en) should be set at the expected location (check the mount directives in the yml file).

```
docker-compose up
```
