FROM python:3.8.2-slim-buster as builder

# silence error messages
ENV TERM linux

# required so that conda can properly init
ENV BASH_ENV ~/.bashrc
SHELL ["/bin/bash", "-c"]

# General installs in the docker
RUN apt-get -y update \
    && apt-get install -y git \
       wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean -y

# Create app directory and copy code
RUN mkdir /home/icubam
WORKDIR /home/icubam

# must copy explicitely to handle cases where image is build in an environment with and without extra files
# (db, config) in the context (e.g., relaunching after a first init).

# TODO:  download code directly in the container from repository/package instead orf relying on local files

# get docker config and move startup scripts for the server and sms containers
COPY docker docker
# copy code and scripts
COPY icubam icubam
COPY scripts scripts

# the resources folder must be mounted

# copy specific files on root folder
COPY LICENSE pyproject.toml README.md requirements.txt requirements-test.txt setup.py conftest.py ./

# pip/setup tools requires version inside .git
COPY .git ./.git

RUN pip install -r requirements.txt &&\
    pip install -r requirements-test.txt &&\
    pip install -e .

# clear pip cache
RUN rm -rf ~/.cache/pip

# make sure final image is clean
FROM builder as launcher

# expose ports for flask app - both server and backoffice
EXPOSE 8888 8890

# default commend when entering the container
ENTRYPOINT ["/bin/bash", "-c"]
# default command
CMD ["./docker/start_server.sh"]
