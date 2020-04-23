#!/bin/bash

# script to install and deploy the ICUBAM app containers locally with a test database
#

# local definitions. The ".env" is automatically loaded by compose.
ENVFILE=".env"
CONFFILE="config.toml"
RESPATH="./resources"


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
  # shellcheck disable=SC1090
  source ${ENVFILE}
else
	echo -e "\n###\nCreate default envvar file ${ENVFILE}"
	touch ${ENVFILE}
	{
    echo "IMAGE_NAME=icubam"
    echo "IMAGE_TAG=latest"
    echo "ICUBAM_COMPOSE_CONTEXT=."
    echo "ICUBAM_CONFIG_FILE=${CONFFILE}"
    echo "ICUBAM_RESOURCES_PATH=${RESPATH}"
    echo "SECRET_COOKIE=_random_string_"
    echo "JWT_SECRET=_random_string_"
    echo "GOOGLE_API_KEY=_random_string_"
    echo "TW_KEY=_random_string_"
    echo "TW_API=_random_string_"
    echo "DB_SALT=_random_string_"
    echo "SMTP_HOST=_random_string_"
    echo "SMTP_USER=_random_string_"
    echo "SMTP_PASSWORD=_random_string_"
    echo "EMAIL_FROM=_random_string_"
  } >> ${ENVFILE}

	echo "Now update the ${ENVFILE} file with the proper values and launch the script again"
	exit 0
fi

# Retrieve Docker image
echo -e "\n###\nRetrieve ICUBAM Docker image ${IMAGE_NAME}:${IMAGE_TAG}"
docker pull "${IMAGE_NAME}":"${IMAGE_TAG}"

# clone the repository and copy the relevant files
echo -e "\n###\Clone repository and copy compose files"
rm -rf icubam docker-compose-core.yml docker-compose-init-db.yml
git clone https://github.com/icubam/icubam.git
cp icubam/docker/docker-compose-init-db.yml .
cp icubam/docker/docker-compose-core.yml .

# Create default folder for resources (configuration file and databases)
mkdir -p resources

# retrieve the default configuration file and move to the resources folder
if [ -f "${RESPATH}/${CONFFILE}" ]; then
    echo -e "\n${RESPATH}/${CONFFILE} exist, use it"i
else
	echo -e "\n###\nGet default config file for containers"
	cp icubam/resources/config.toml ${RESPATH}/${CONFFILE}

	echo "Now update the ${RESPATH}/${CONFFILE} file with the proper values and launch the script again"
  exit 0
fi

# remove the cloned repository
rm -rf icubam

# Initialize the default test database
echo -e "\n###\nInitialize fake database"
docker-compose -f docker-compose-init-db.yml --project-directory . up
docker-compose -f docker-compose-init-db.yml --project-directory . down

# launch the icubam services
echo -e "\n###\nLaunch app containers"
docker-compose -f docker-compose-core.yml  --project-directory . up -d


