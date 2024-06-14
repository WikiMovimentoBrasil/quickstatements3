# quickstatements3

Repository for the development of a new version of QuickStatements

## Local development HOW TO

Required tools:

* Docker
* Make

To build the development container

```bash
> make build
```

To run a shell inside the container

```bash
> make shell
```

Make sure that you have an env file inside the local etc/ dir. This file contains all the **ENVIRONMENT VARIABLES** used by the system and must never be added to your git repo.

To generate a good secret key you can run with python 3.6+

```
python -c "import secrets; print(secrets.token_urlsafe())"
```

If you are running this container for the first time, you have to initialize the database and create a superuser for the Django ADMIN

```bash
> cd src
> python manage.py migrate
> python manage.py createsuperuser
```

Now that everything is set up, we can start **Quickstatements**. We have 2 ways of doing that:

* from inside the container, running 
```bash 
>./cmd_run.sh
```
* from our Makefile, running 
```bash 
> make run
```

Now **Quickstatements** is available at http://localhost:8765/
