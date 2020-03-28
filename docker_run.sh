#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 2 ]
then
	  echo "usage: $0 IMAGE_NAME PORT"
	  echo "   where IMAGE_NAME is the image name and tage to use"
	  echo "   where PORT is the local port number where to map the port of the server on the container"
      echo ""
      echo "   example: $0 ivubam:1.0 9000"
	  exit
fi

docker run -dt -p $2:8888 $1

echo use docker logs to get the activation URL

