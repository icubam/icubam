#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 2 ]
then
	  echo "usage: $0 IMAGE_NAME ENV"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where ENV can be dev, prod"
      echo ""
      echo "   example: $0 icubam:1.0 dev"
	  exit
fi

docker run -dt \
    --name icubam-sms \
    --mount type=bind,source="$(pwd)"/resources/config.toml,target=/resources/config \
    --mount type=bind,source="$(pwd)"/icubam.db,target=/home/icubam/icubam.db \
    --mount type=bind,source="$(pwd)"/test.db,target=/home/icubam/test.db \
    --mount type=bind,source="$(pwd)"/resources/token.pickle,target=/home/icubam/resources/token.pickle \
    --env-file docker/icubam-container.env \
    --env ENV_MODE=$2
    $1  \
    ./start_server_sms.sh
