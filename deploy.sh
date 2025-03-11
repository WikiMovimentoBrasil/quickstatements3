#!/bin/bash

set -eu

PROJECT_DIR="${HOME}/www/python"
SRC_DIR="${PROJECT_DIR}/src"

cd "${PROJECT_DIR}" || exit

echo "==> Updating git repository..."
git pull

echo "==> Entering python shell..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  echo "==> Installing dependencies..." && \
  export MYSQLCLIENT_CFLAGS="-I/usr/include/mariadb/" && \
  export MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu/ -lmariadb" && \
  webservice-python-bootstrap && \
  source "${PROJECT_DIR}/venv/bin/activate" && \
  echo "==> Running migrations..." && \
  python3 "${SRC_DIR}/manage.py" migrate && \
  echo "==> Collecting static files..." && \
  python3 "${SRC_DIR}/manage.py" collectstatic --noinput

echo "==> Restarting webservice..."
toolforge webservice --backend=kubernetes --mem 6Gi python3.11 restart

echo "==> Restarting batches..."
toolforge webservice --backend=kubernetes python3.11 shell -- \
  webservice-python-bootstrap  && \
  source "${PROJECT_DIR}/venv/bin/activate" && \
  python3 "${SRC_DIR}/manage.py" restart_batches
