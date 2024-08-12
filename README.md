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

## OAuth

This application uses OAuth2 with the Mediawiki provider.

The grants we probably need are

* Perform high volume activity
  * High-volume (bot) access
* Interact with pages
  * Edit existing pages
  * Edit protected pages (risk rating: vandalism)
  * Create, edit, and move pages

### Consumer

After registering a consumer in

<https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration>

This application is listening on `/auth/callback/`, so, when registering, define the callback endpoint as `https://yourdomain.com/auth/callback/`.

After receveing the consumer id and secret, setup `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` environment variables.

### Developer access

If you want to login with a developer access token, you need to register for yourself an owner-only consumer application for OAuth2. Follow the form and be sure to tick "This consumer is for use only by <YOUR USERNAME>".

## Toolforge deployment

* Login and enter into the tool user
* Clone the repository at `~/www/python/`
* Update `uwsgi.ini` with the toolname. In this case, its `qs-dev`
* Create the environment variables file at `~/www/python/src/.env` with `install -m 600 /dev/null ~/www/python/src/.env` so that only your user can read it.
* Run `deploy.sh`
* Logs are at `~/uwsgi.log`
