#!/usr/bin/env bash

sudo service nginx start
cd /home/wmb/www && poetry run django-admin collectstatic --no-input && chmod -R 777 /home/wmb/www/static
cd /home/wmb/www && poetry run django-admin migrate --no-input
cd /home/wmb/www && poetry run uwsgi --ini app.ini
