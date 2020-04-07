# Docker deployment

This folder contains the scripts and configurations required to launch the application in Docker containers, either

- individually (for debugging purposes, using the `docker/scripts/docker_build.sh`, `docker/scripts/docker_run.sh` and
`docker/scripts/docker_sms_build.sh` scripts), 
- or as a deployment of the application using the
`docker/docker-compose.yml` script (for a host/VM without nginx/proxy), or the `docker/docker-compose-core.yml` script
if the host/VM already has nginx installed or an equivalent proxy.

Files/folders are mounted (bind) in the containers (nginx/certbot) defined in the `docker-compose.yml`file.

Change the environement variable `ENV_MODE` depending on the targeted environment (dev, prod, ...) . 
The `--mode=$ENV_MODE` command line parameter when starting the icubam server and sms apps is set using this environment 
variable (check the files `start_server.sh` and `start_server_sms.sh`).

## Docker compose

To start properly, the application requires
- The ICUBAM environment variables to be set in the shell.
- The production and test databases to be generated and available at the root of the project (`icubam.db` and `test.db`)
- The `resources/token.pickle` file to be in the `resources` folder

For a full deployment with Nginx
1. replace WEB_HOSTNAME in Nginx configuration files with `set_hostname_nginx.sh` (from within the docker/scripts folder).
2. copy `app.conf.init` as `app.conf` in the `docker/configs/nginx` folder.
3. check `docker/scripts/init-letsencrypt.sh` for any change (esp. email address) and execute it from the root of the project. This generates the initial certificate
4. stop and terminate the nginx container (necessary to reload the config).
5. copy either `app.conf.dev` or `app.conf.prod` as `app.conf` in the `docker/configs/nginx` folder.
6. ensure all the required environment variables are set
7. from the root of the project, launch the containers with  `docker-compose -f docker/docker-compose.yml --project-directory . up`

### Nginx/Certbot setup

The LetsEncryot/certbot setup is based on https://github.com/wmnnd/nginx-certbot.

The `configs` folder stores nginx/certbot configuration files for ssl connection support.
Certbot configuration files are added at runtime when generating/updating the ssl certificate.

Two nginx configurations are provided, 
- a `dev` file for testing locally, that only supports http (change https to http 
and remove port 8888 when using the link provided by the running server).
- a `prod` file that manages ssl connections for testing on an internet reachable host. Depending on the deployment server name, changes to the `nginx/app.conf` file are required.
In particular, WEB_HOSTNAME should be replaced with the targeted's URL hostname (e.g., www.example.org)
for both the `server_name` and also in the path for the ssl certificates.
- an `init` configuration used in the first initialization step of the Let'sEncryp/Certbot setup.

To replace the WEB_HOSTNAME with the proper hostname, a script is provided in the `scripts` folder.

Compared to the initial `init-letsencrypt.sh`script, explicit setup of the docker-compose.yml file and root path has been added as all the docker related files are in a specific subfolder.


### Launching the app

The complete application's containers can be launched using docker compose, either in a full version that also starts 
nginx and certbot for managin ssl connections (to deploy on à clean VM/host), or just the containers for the app 
and sms servers in case the VM/host used for the deployment already handles ingress communications (e.g., nginx 
deployed on the VM/host).

The two compose files are
- `docker-compose.yml` for the full version
- `docker-compose-core.yml` for the app only containers version

To launch the complete install (server, sms server, nginx, certbot containers), use the 
`docker-compose up` command, from the root of the project, specifiying explicitely the root
as the configuration file is in a subfolder.

```
docker-compose -f docker/docker-compose-core.yml --project-directory .  up
```

### Environment variables

Environment variables are not set in the Docker image, but set when starting the Docker containers. The containers expect the following variables to be set in order to launch

    ENV_MODE (can be prod or dev)
    SHEET_ID
    TOKEN_LOC  (full path location of the token.pickle file)
    SECRET_COOKIE
    JWT_SECRET
    GOOGLE_API_KEY
    TW_KEY
    TW_API

There are multiple ways for setting up these variables.
- have a .env file at the root of the project
- set the environment variables in the shell (e.g., to manage different configurations stored in another location)
prior to launching the docker-compose.

Rules of precedence
- If variables **not set** in the environment and **no .env file**, the containers start and fail due to missing variables.
- If variables **set** in the environment but **no .env file**, the containers start with the values set in the environment variables.
- If variables **not set** in the environment but **.env file** exists, the containers start with the values set in the .env file.
- If variables **set** in the environment and **.env file** exists, the containers start with the values set in the environment variables.

Note: in order to reload the configuration, the containers (not the image) must be terminated and recreated (not only stop/start).

Note: One way to quickly set environment variables from a dedicated file
```
set -a
. $HOMR/icubam_secrets/envars-production.env
set -a
```

### Docker commands

Remove/force the icubam containers
```
docker rm -f icubam-server icubam-sms-server
```

Get the logs of the server
```
docker logs icubam-server
```

Delete the server container image
```
docker rmi icubam-server
```

To debug a container, in another shell, enter the server container in interactive mode to check the files are at their expected location (using `docker exec -it icubam-server bash` or 
```
docker exec -it icubam-server "ls -la"`
docker exec -it icubam-server bash`
```

### Issues and debug


- After changes in configuration files, make sure a stopped container with the current name do not exist 
 - Check the files being mounted do exists (hint : if they do not exist, a folder with this name is automatically created by compose).
- If changes done to configuration files are not visible/performed, check that the proper yml file is used in compose
- If no URL appears in the log, but the server is otherwise starting properly, the issue usually lies in the database (either not present, or wrong format)
