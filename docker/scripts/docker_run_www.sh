#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 2 ]
then
	  echo "usage: ${0} IMAGE_NAME PORT"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where PORT is the local port number where to map the port of the server on the container"
      echo ""
      echo "   example: ${0} icubam:1.0 9000"
	  exit
fi

if [ ! -f "$(pwd)"/resources/"${ICUBAM_CONFIG_FILE}" ]; then
    echo "Config file (toml) not found!"
    exit
fi

docker run -d -p "${2}":8888 \
    --name icubam_www_server \
    --mount type=bind,source="$(pwd)"/resources,target=/home/icubam/resources \
    --env ICUBAM_CONFIG_FILE="${ICUBAM_CONFIG_FILE}" \
    --env SECRET_COOKIE="${SECRET_COOKIE}" \
    --env JWT_SECRET="${JWT_SECRET}" \
    --env GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --env TW_KEY="${TW_KEY}" \
    --env TW_API="${TW_API}" \
    --env DB_SALT="${DB_SALT}" \
    "${1}" \
    ./docker/start_server_www.sh
