#
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

# copy all files (alternatively, git clone with commit or wget)
COPY . ./

COPY ./docker/start_server.sh .
COPY ./docker/start_server_sms.sh .

RUN  mkdir -p resources
COPY ./resources/config.toml resources

# prepare for the conda environment
RUN echo ".  /root/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
RUN conda create -n icubam python=3.8
RUN conda activate icubam && pip install -r requirements.txt && pip install -e .

# default commend when entering the container
ENTRYPOINT ["/bin/bash", "-c"]
# default command
CMD ["./start_server.sh"]