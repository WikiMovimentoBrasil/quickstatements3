.PHONY: build init shell run test integration

build:
	pip install poetry; \
	poetry install -E dev;

init: build
	poetry run django-admin migrate; \
	poetry run django-admin createsuperuser

shell:
	poetry run django-admin shell

run:
	poetry run django-admin migrate --no-input; \
	poetry run django-admin collectstatic --no-input; \
	poetry run django-admin runserver

test:
	poetry run pytest

integration:
	poetry run pytest -k IntegrationTests
