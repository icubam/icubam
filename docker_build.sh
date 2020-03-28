#!/usr/bin/env bash

# check that all required parameters are provided
if [ $# -ne 3 ]
then
	  echo "usage: $0 CONFIGS_FILENAME IMAGE_VERSION ENV"
	  echo "   where CONFIGS_FILENAME is the archive with all the configuration files"
	  echo "   where IMAGE_VERSION is the version number for the Docker image being built"
	  echo "   where ENV can be dev, prod"
      echo ""
      echo "   example: $0 ../configs_deply.tgz 1.0 dev"
	  exit
fi

docker build -f Dockerfile  -t="icubam:$2" . --build-arg BUILD_TARGET=$2 --build-arg CONFIGS_FILE=$1

