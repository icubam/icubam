#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 2 ]
then
	  echo "usage: ${0} IMAGE_NAME PORT"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where PORT is the local port number where to map the port of the server on the container"
      echo ""
      echo "   example: ${0} icubam:1.0 9000 dev"
	  exit
fi

echo '========================================='
echo 'Check the console to get the activation URL with docker logs'
echo 'Attention:'
echo '   replace the default port 8888 in the URL with the defined port'
echo '========================================='

if [ ! -f "$(pwd)"/resources/config.toml ]; then
    echo "resources/config.toml not found!"
    exit
fi
if [ ! -f "$(pwd)"/icubam.db ]; then
    echo "icubam.db not found!"
    exit
fi
if [ ! -f "$(pwd)"/test.db ]; then
    echo "test.db not found!"
    exit
fi


docker run -d -p "${2}":8888 \
    --name icubam-server \
    --mount type=bind,source="$(pwd)"/resources/config.toml,target=/home/icubam/resources/config.toml \
    --mount type=bind,source="$(pwd)"/icubam.db,target=/home/icubam/icubam.db \
    --mount type=bind,source="$(pwd)"/test.db,target=/home/icubam/test.db \
    --env ENV_MODE="${ENV_MODE:-prod}" \
    --env SECRET_COOKIE="${SECRET_COOKIE}" \
    --env JWT_SECRET="${JWT_SECRET}" \
    --env GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    --env TW_KEY="${TW_KEY}" \
    --env TW_API="${TW_API}" \
    "${1}" \
    ./start_server.sh
