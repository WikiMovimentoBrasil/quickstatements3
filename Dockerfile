FROM python:3.12
LABEL maintainer="Miguel Galves <mgalves@gmail.com>"

# Install system dependencies
RUN apt-get update && apt-get -y install sudo gettext

# Creating our local user and group
RUN adduser --disabled-password --home /home/wmb --shell /bin/bash wmb
RUN adduser wmb sudo

# We dont want any password when running SUDO
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# changing to our local user
USER wmb
RUN mkdir -p /home/wmb/www/{src,static}

COPY requirements.txt /home/wmb/www
RUN sudo chown wmb:wmb -R /home/wmb/www

WORKDIR /home/wmb/www/

RUN pip install -r requirements.txt

ENV PATH="${PATH}:/home/wmb/.local/bin"
ENV DJANGO_SETTINGS_MODULE=qsts3.settings
ENV PYTHONPATH="${PYTHONPATH}:/home/wmb/www/src"

WORKDIR /home/wmb/www/src
