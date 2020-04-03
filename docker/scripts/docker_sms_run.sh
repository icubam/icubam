#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 2 ]
then
	  echo "usage: $0 IMAGE_NAME PENENVVORT"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where ENV can be dev, prod"
      echo ""
      echo "   example: $0 icubam:1.0 prod"
	  exit
fi

docker run -dt \
    --name icubam-sms \
    --mount type=bind,source="$(pwd)"/docker/configs/resources/icubam.env,target=/home/icubam/resources/icubam.env \
    --mount type=bind,source="$(pwd)"/docker/configs/resources/icubam.toml,target=/home/icubam/resources/icubam.toml \
    --mount type=bind,source="$(pwd)"/resources/icubam.db,target=/home/icubam/resources/icubam.db \
    --mount type=bind,source="$(pwd)"/resources/token.pickle,target=/home/icubam/resources/token.pickle \
    --env ENV_MODE=$2
    $1  \
    ./start_server_sms.sh
