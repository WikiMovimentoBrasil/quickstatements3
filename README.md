# quickstatements3

Repository for the development of a new version of QuickStatements

## Local development HOW TO

Required tools:

* Docker
* Make

To build the development container

> make build

To run a shell inside the container

> make shell

Make sure that you have an env file inside the local etc/ dir. This file contains all the ENVIRONMENT VARIABLES used by the system and must never be added to your git repo.

If you are running this container for the first time, you have to initialize the database and create a superuser for the Django ADMIN

> cd src
> python manage.py migrate
> python manage.py createsuperuser


Now that everything is set up, we can start quickstatements. We have 2 ways of doing that:

* from inside the container, running ./cmd_run.sh
* from our Makefile, running make run

Now Quickstatements is available at http://localhost:8765/