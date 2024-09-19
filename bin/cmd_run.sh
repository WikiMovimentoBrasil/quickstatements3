#!/usr/bin/env bash

sudo service nginx start
cd /home/wmb/www/src && python3 manage.py collectstatic --no-input && chmod -R 777 /home/wmb/www/src/static
cd /home/wmb/www/src && python3 manage.py migrate --no-input
cd /home/wmb/www/src && uwsgi --ini app.ini