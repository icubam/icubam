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
if [ ! -f "$(pwd)"/resources/token.pickle ]; then
    echo "resources/token.pickle not found!"
    exit
fi

docker run -dt \
    --name icubam-sms \
    --mount type=bind,source="$(pwd)"/resources/config.toml,target=/home/icubam/resources/config.toml \
    --mount type=bind,source="$(pwd)"/icubam.db,target=/home/icubam/icubam.db \
    --mount type=bind,source="$(pwd)"/test.db,target=/home/icubam/test.db \
    --mount type=bind,source="$(pwd)"/resources/token.pickle,target=/home/icubam/resources/token.pickle \
    --env ENV_MODE=$2
    --env TOKEN_LOC="/home/icubam/resources/token.pickle" \
    --env SHEET_ID=$SHEET_ID \
    --env SMS_KEY=$SMS_KEY \
    --env SECRET_COOKIE=$SECRET_COOKIE \
    --env JWT_SECRET=$JWT_SECRET \
    --env GOOGLE_API_KEY=$GOOGLE_API_KEY \
    --env MB_KEY=$MB_KEY \
    --env NX_KEY=$NX_KEY \
    --env NX_API=$NX_API \
    --env TW_KEY=$TW_KEY \
    --env TW_API=$TW_API \
    $1  \
    ./start_server_sms.sh
