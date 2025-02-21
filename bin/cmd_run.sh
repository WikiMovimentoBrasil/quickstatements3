#!/usr/bin/env bash


echo "Giving ${DB_USER} all privileges on test_${DB_NAME} database"
sudo apt install mariadb-client -y
mariadb --host="${DB_HOST}" --database="${DB_NAME}" --user=root -p"${DB_ROOT_PASSWORD}" --execute="GRANT all privileges ON test_${DB_NAME}.* TO '${DB_USER}'@'%';"
sudo apt purge mariadb-client -y

sudo service nginx start
cd /home/wmb/www/src && python3 manage.py collectstatic --no-input && chmod -R 777 /home/wmb/www/src/static
cd /home/wmb/www/src && python3 manage.py migrate --no-input
cd /home/wmb/www/src && uwsgi --ini app.ini