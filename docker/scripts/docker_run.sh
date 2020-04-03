#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 3 ]
then
	  echo "usage: $0 IMAGE_NAME PORT ENV"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where PORT is the local port number where to map the port of the server on the container"
	  echo "   where ENV can be dev, prod"
      echo ""
      echo "   example: $0 icubam:1.0 9000 dev"
	  exit
fi

echo '========================================='
echo 'Check the console to get the activation URL with docker logs'
echo 'Attention:'
echo '   replace the default port 8888 in the URL with the defined port'
echo '========================================='

docker run -d -p $2:8888 \
    --name icubam-server \
    --mount type=bind,source="$(pwd)"/resources/config.toml,target=/resources/config \
    --mount type=bind,source="$(pwd)"/icubam.db,target=/home/icubam/icubam.db \
    --mount type=bind,source="$(pwd)"/test.db,target=/home/icubam/test.db \
    --mount type=bind,source="$(pwd)"/resources/token.pickle,target=/home/icubam/resources/token.pickle \
    --env-file docker/icubam-container.env \
    --env ENV_MODE=$3 \
     $1  \
    ./start_server.sh
