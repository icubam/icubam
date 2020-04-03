# Docker deployment


Folder used to store nginx/certbot configuration files for ssl connection support (not used directly by icubam).
Certbot configuration files are added at runtime when generating/updating the ssl certificate.

Two nginx configurations are provided, 
- a `dev` file for testing locally, that only supports http (change https to http 
and remove port 8888 when using the link provided by the running server).
- a `prod` file that manages ssl connections for testing on an internet reachable host. Depending on the deployment server name, changes to the `nginx/app.conf` file are required.
In particular, WEB_HOSTNAME should be replaced with the targeted's URL hostname (e.g., www.example.org)
for both the `server_name` and also in the path for the ssl certificates.

Files/folders are mounted (bind) in the containers (nginx/certbot) defined in the docker-compose.yml.

Depending on the deployment mode, (prod, dev, ...) change the environement variable `ENV_MODE` in the `docker-compose.yml` file. 
The `--mode=$ENV_MODE` command line parameter when starting the icubam server and sms apps is set using this environment 
variable (check the files `start_server.sh` and `start_server_sms.sh`).


## Docker compose

The complete application's containers can be launched using docker compose, either in a full version that also starts 
nginx and certbot for managin ssl connections (to deploy on à clean VM/host), or just the containers for the app 
and sms servers in case the VM/host used for the deployment already handles ingress communications (e.g., nginx 
deployed on the VM/host).
The two compose files are
- docker-compose.yml for the full version
- docker-compose-core.yml for the app only containers version

To launch the complete install (server, sms server, nginx, certbot containers), use the `docker-compose -f FILE up` command
