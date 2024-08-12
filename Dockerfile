FROM python:3.12
LABEL maintainer="Miguel Galves <mgalves@gmail.com>"

# We need sudo and nginx to run
RUN apt-get update && apt-get -y install sudo nginx emacs

# Creating our local user and group
RUN groupadd nginx
RUN adduser --disabled-password --home /home/wmb --shell /bin/bash wmb 
RUN adduser wmb sudo
RUN adduser wmb nginx

# We dont want any password when running SUDO
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# NGINX configuration
COPY etc/nginx.conf /etc/nginx/sites-enabled/default

# changing to our local user
USER wmb
RUN mkdir /home/wmb/logs && chmod 777 /home/wmb/logs && chown wmb:nginx /home/wmb/logs
RUN mkdir /home/wmb/logs/nginx && chmod 777 /home/wmb/logs/nginx && chown wmb:nginx /home/wmb/logs/nginx
RUN mkdir /home/wmb/www
RUN mkdir /home/wmb/www/src

# Needed for nginx
RUN chmod o+x /home/wmb &&chmod o+x /home/wmb/www

COPY bin/cmd_run.sh /home/wmb/www 
RUN sudo chown wmb:wmb /home/wmb/www/cmd_run.sh && sudo chmod 777 /home/wmb/www/cmd_run.sh

COPY requirements.txt /home/wmb/www
RUN sudo chown wmb:wmb /home/wmb/www/requirements.txt

WORKDIR /home/wmb/www/

RUN pip install -r requirements.txt

ENV PATH="${PATH}:/home/wmb/.local/bin"

EXPOSE 8000 80

