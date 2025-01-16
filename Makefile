
export ROOT_DIR=${PWD}
export IMAGE=quickstatements3:dev

VERSION ?= $(shell date +"%Y%m%d_%H%M")


build:
	docker build -t ${IMAGE} -f Dockerfile .


shell: 
	docker run --rm -ti --env-file etc/env -p 8765:80 -p 8000:8000 -v ${ROOT_DIR}/src:/home/wmb/www/src ${IMAGE} bash

run: 
	docker run --rm -ti --env-file etc/env -p 8765:80 -p 8000:8000 -v ${ROOT_DIR}/src:/home/wmb/www/src ${IMAGE} /home/wmb/www/cmd_run.sh

test:
	docker run --rm -ti --env-file etc/env -v ${ROOT_DIR}/src:/home/wmb/www/src ${IMAGE} bash -c "cd src; python3 manage.py test"

integration:
	docker run --rm -ti --env-file etc/env -v ${ROOT_DIR}/src:/home/wmb/www/src ${IMAGE} bash -c "cd src; python3 manage.py test integration"
