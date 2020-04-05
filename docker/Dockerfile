# ARG required due to build option in docker-compose
ARG ENV_MODE

FROM ubuntu:18.04

# silence error messages
ENV TERM linux

# required so that conda can properly init
ENV BASH_ENV ~/.bashrc
SHELL ["/bin/bash", "-c"]

# comment out the line in the default .bashrc that does an early exit if not in
# interactive mode. It should be noted that the -i option of docker run does
# not launch the shell in interactive mode. CCheck Dockerfile.3 for a demo.
RUN sed -e '/[\ -z \"\$PS1\"\ ]\ &&\ return/ s/^#*/#/' -i /root/.bashrc

# General installs in the docker
RUN apt-get -y update && apt-get -y upgrade

RUN apt-get -y install \
    apt-utils \
    build-essential \
    software-properties-common

RUN apt-get install -y \
    curl \
	git \
	screen \
	ufw \
    vim \
	wget

# Install miniconda and add to PATH
RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN sh Miniconda3-latest-Linux-x86_64.sh -b
ENV PATH /root/miniconda3/bin:$PATH

# expose ports for flask app
EXPOSE 8888

# Create app directory and copy code
RUN mkdir /home/icubam
WORKDIR /home/icubam

# must copy explicitely to handle cases where image is build in an environment without extra files (db, config)
# or with extra file (e.g., after a first init).
# TODO:  download code directly in the container from repository/package instead orf relying on local files

# get docker config and move startup scripts for the server and sms containers
COPY docker docker
RUN mv ./docker/start_server.sh .
RUN mv ./docker/start_server_sms.sh .
# copy code and scripts
COPY icubam icubam
COPY scripts scripts
# create resource folder
RUN  mkdir resources
# copy specific files on root folder
COPY dev_install.md LICENSE pyproject.toml README.md requirements.txt setup.py ./
# pip/setup tools requires version inside .git
COPY .git ./.git

# prepare for the conda environment
RUN echo ".  /root/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
RUN conda create -n icubam python=3.8
RUN conda activate icubam && pip install -r requirements.txt && pip install -e .

# default commend when entering the container
ENTRYPOINT ["/bin/bash", "-c"]
# default command
CMD ["./start_server.sh"]
