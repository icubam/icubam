#!/bin/bash

# script to install and deploy the ICUBAM app containers locally with a test database
#

# local definitions. The ".env" is automatically loaded by compose.
ENVFILE=".env"
CONFFILE="config.toml"

# check that docker is indeed installed
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi
if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

# envvar file
if [ -f "${ENVFILE}" ]; then
  echo -e "\n${ENVFILE} exist, load envvars"i
  source ${ENVFILE}
else
	echo -e "\n###\nCreate default envvar file ${ENVFILE}"
	touch ${ENVFILE}
	echo "IMAGE_NAME=icubam" >> ${ENVFILE}
	echo "IMAGE_TAG=latest" >> ${ENVFILE}
	echo "ICUBAM_COMPOSE_CONTEXT=." >> ${ENVFILE}
	echo "ICUBAM_CONFIG_FILE=${CONFFILE}" >> ${ENVFILE}
	echo "SECRET_COOKIE=_random_string_" >> ${ENVFILE}
	echo "JWT_SECRET=_random_string_" >> ${ENVFILE}
	echo "GOOGLE_API_KEY=_random_string_" >> ${ENVFILE}
	echo "TW_KEY=_random_string_" >> ${ENVFILE}
	echo "TW_API=_random_string_" >> ${ENVFILE}
	echo "DB_SALT=_random_string_" >> ${ENVFILE}

	echo "Now update the ${ENVFILE} file with the proper values and launch the script again"
	exit 0
fi

# Retrieve Docker image
echo -e "\n###\nRetrieve ICUBAM Docker image ${IMAGE_NAME}:${IMAGE_TAG}"
docker pull ${IMAGE_NAME}:${IMAGE_TAG}

# Retrieve docker-compose files - assume there is an external reverse-proxy facility for the deployment
echo -e "\n###\nDownload compose files"
rm -f docker-compose-core.yml docker-compose-init-db.yml
wget https://raw.githubusercontent.com/icubam/icubam/master/docker/docker-compose-init-db.yml
wget https://raw.githubusercontent.com/icubam/icubam/master/docker/docker-compose-core.yml

# Create default folder for resources (configuration file and databases)
mkdir -p resources

# retrieve the default configuration file and move to the resources folder
if [ -f "resources/${CONFFILE}" ]; then
    echo -e "\nresources/${CONFFILE} exist, use it"i
else
	echo -e "\n###\nGet default config file for containers"
	wget https://raw.githubusercontent.com/icubam/icubam/master/resources/config.toml
	mv config.toml resources

	echo "Now update the ${CONFFILE} file with the proper values and launch the script again"
  exit 0
fi

# Initialize the default test database
echo -e "\n###\nInitialize fake database"
docker-compose -f docker-compose-init-db.yml --project-directory . up
docker-compose -f docker-compose-init-db.yml --project-directory . down

# launch the icubam services
echo -e "\n###\nLaunch app containers"
docker-compose -f docker-compose-core.yml  --project-directory . up -d


