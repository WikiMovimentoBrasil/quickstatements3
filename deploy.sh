#!/bin/bash

set -eu

cd ~/www/python || exit

echo "==> Updating git repository..."
git pull

echo "==> Entering python shell..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  webservice-python-bootstrap && \
  echo "==> Installing dependencies..." && \
  pip install poetry && poetry install && \
  echo "==> Running migrations..." && \
  django-admin migrate && \
  echo "==> Collecting static files..." && \
  django-admin collectstatic --noinput

echo "==> Restarting webservice..."
toolforge webservice --backend=kubernetes python3.11 restart
