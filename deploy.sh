#!/bin/bash

set -eu

cd ~/www/python || exit

echo "==> Updating git repository..."
git pull

echo "==> Entering python shell..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  webservice-python-bootstrap && \
  source venv/bin/activate && \
  echo "==> Running migrations..." && \
  python3 src/manage.py migrate && \
  echo "==> Collecting static files..." && \
  python3 src/manage.py collectstatic --noinput

echo "==> Restarting webservice..."
toolforge webservice --backend=kubernetes python3.11 restart
