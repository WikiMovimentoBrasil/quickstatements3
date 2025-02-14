# quickstatements3

Repository for the development of a new version of QuickStatements

## Local development HOW TO

You need to create a python virtualenv and activate. The provided Makefile assumes that you are executing the commands with the active virtualenv

Create a `.env` file to define the needed **environment variables** required. The `.env.sample` can be used as a template.


To generate a good secret key you can run with python 3.6+

```
python -c "import secrets; print(secrets.token_urlsafe())"
```

If you are running this container for the first time, you have to initialize the database and create a superuser for the Django admin.

```bash
make init
```

With everything set up, we can start **Quickstatements**. The easiest way to do it is via `make run`


Now **Quickstatements** is available at http://localhost:8000/

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

### Integration tests

To run Integration tests on https://test.wikidata.org, you'll need a developer access token (owner-only) to edit on `test.wikidata.org`.

After obtaining it, define the environment variable `INTEGRATION_TEST_AUTH_TOKEN` in `.env` file as your developer access token. Then, run the tests with `make integration`.

## Toolforge deployment

* Login and enter into the tool user
* Clone the repository at `~/www/python/`
* Update `uwsgi.ini` with the toolname. In this case, its `qs-dev`
* Create the environment variables file at `~/www/python/.env` with `install -m 600 /dev/null ~/www/python/.env` so that only your user can read it.
* Run `deploy.sh`
* Logs are at `~/uwsgi.log`
