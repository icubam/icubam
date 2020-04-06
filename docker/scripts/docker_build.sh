#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 1 ]
then
	  echo "usage: $0 IMAGE_VERSION"
	  echo "   where IMAGE_VERSION is the version number for the Docker image being built"
      echo ""
      echo "   example: $0 1.0"
	  exit
fi

docker build -f ./docker/Dockerfile  -t="icubam:$1" .

