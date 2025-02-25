#!/bin/bash

set -eu

cd ~/www/python || exit

echo "==> Updating git repository..."
git pull

echo "==> Entering python shell..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  webservice-python-bootstrap && \
  source venv/bin/activate && \
  echo "==> Installing dependencies..." && \
  export MYSQLCLIENT_CFLAGS="-I/usr/include/mariadb/" && \
  export MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu/ -lmariadb" && \
  pip install -r requirements.txt && \
  echo "==> Running migrations..." && \
  python3 src/manage.py migrate && \
  echo "==> Collecting static files..." && \
  python3 src/manage.py collectstatic --noinput

echo "==> Restarting webservice..."
toolforge webservice --backend=kubernetes python3.11 restart

echo "==> Restarting batches..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  webservice-python-bootstrap && \
  source venv/bin/activate && \
  python3 src/manage.py restart_batches
