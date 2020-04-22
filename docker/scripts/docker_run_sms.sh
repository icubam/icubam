#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 1 ]
then
	  echo "usage: ${0} IMAGE_NAME"
	  echo "   where IMAGE_NAME is the image name and tage to use"
      echo ""
      echo "   example: ${0} icubam:1.0"
	  exit
fi

if [ ! -f "$(pwd)"/resources/"${ICUBAM_CONFIG_FILE}" ]; then
    echo "Config file (toml) not found!"
    exit
fi

docker run -dt \
    --name icubam_sms_server \
    --mount type=bind,source="$(pwd)"/resources,target=/home/icubam/resources \
    --env ICUBAM_CONFIG_FILE="${ICUBAM_CONFIG_FILE}" \
    --env SECRET_COOKIE="${SECRET_COOKIE}" \
    --env JWT_SECRET="${JWT_SECRET}" \
    --env GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --env TW_KEY="${TW_KEY}" \
    --env TW_API="${TW_API}" \
    --env DB_SALT="${DB_SALT}" \
    "${1}" \
    ./docker/start_server_sms.sh
