# Docker deployment

Folder used to store nginx/certbot configuration files for ssl connection support (not used directly by icubam).
Certbot configuration files are added at runtime when generating/updating the ssl certificate.

Two nginx configurations are provided, 
- a `dev` file for testing locally, that only supports http (change https to http 
and remove port 8888 when using the link provided by the running server).
- a `prod` file that manages ssl connections for testing on an internet reachable host. Depending on the deployment server name, changes to the `nginx/app.conf` file are required.
In particular, WEB_HOSTNAME should be replaced with the targeted's URL hostname (e.g., www.example.org)
for both the `erver_name` and also in the path for the ssl certificates.

Files/folders are mounted (bind) in the containers (nginx/certbot) defined in the docker-compose.yml.

Depending on the deployment mode, (prod, dev, ...) change the environement variable `ENV_MODE` in the `docker-compose.yml` file. 
The `--mode=$ENV_MODE` command line parameter when starting the icubam server and sms apps is set using this environment 
variable (check the files `start_server.sh` and `start_server_sms.sh`).

