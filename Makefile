
export ROOT_DIR=${PWD}
export IMAGE=quickstatements3:dev

VERSION ?= $(shell date +"%Y%m%d_%H%M")


build:
	docker build -t ${IMAGE} -f Dockerfile .

run:
	docker-compose up -d

shell:
	docker-compose exec app bash

watch:
	docker-compose logs app -f

test:
	docker-compose exec app django-admin test

integration:
	docker-compose exec app django-admin test integration
