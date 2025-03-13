#!/bin/bash

set -eu

PROJECT_DIR="${HOME}/www/python"
SRC_DIR="${PROJECT_DIR}/src"
POD="$(kubectl get pods -n tool-qs-dev -o name| head -n1 | cut -d/ -f2)"

cd "${PROJECT_DIR}" || exit 1

echo "==> Updating git repository..."
git pull

echo "==> Entering python shell..."
kubectl exec "${POD}" -- bash -euc \
"
  echo '==> Installing dependencies...' && \
  export MYSQLCLIENT_CFLAGS='-I/usr/include/mariadb/' && \
  export MYSQLCLIENT_LDFLAGS='-L/usr/lib/x86_64-linux-gnu/ -lmariadb' && \
  webservice-python-bootstrap && \
  source \"${PROJECT_DIR}/venv/bin/activate\" && \
  echo '==> Running migrations...' && \
  python3 \"${SRC_DIR}/manage.py\" migrate && \
  echo '==> Collecting static files...' && \
  python3 \"${SRC_DIR}/manage.py\" collectstatic --noinput
"

echo '==> Restarting webservice...'
toolforge webservice --backend=kubernetes --mem 4Gi python3.11 restart

echo '==> Pausing briefly to allow the container to start...'
sleep 10

POD="$(kubectl get pods -n tool-qs-dev -o name| head -n1 | cut -d/ -f2)"
echo '==> Restarting batches...'
kubectl exec "${POD}" -- bash -euc \
"
  source \"${PROJECT_DIR}/venv/bin/activate\" && \
  python3 \"${SRC_DIR}/manage.py\" restart_batches
"