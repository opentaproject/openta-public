SHELL=/usr/bin/env bash
UID:=$(shell id -u)
GID:=$(shell id -g)
REVISION:=$(shell git rev-parse HEAD)$(shell git diff --no-color | md5sum)
COMMIT:=$(shell git rev-parse --abbrev-ref HEAD)_$(shell git rev-parse --short HEAD)

define run_docker
	@docker run --rm -it -u $(UID):$(GID) -v $(PWD):/openta $(1) $(2) $(3)
endef

define run_docker_backend
	$(call run_docker, -w /openta/django/backend $(1), openta/backend:latest, $(2))
endef

define run_docker_frontend
	$(call run_docker, -w /openta/frontend $(1), openta/frontend:latest, $(2))
endef

error:
	@$(MAKE) list

.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null \
		| awk -v RS= -F: '/^# File/,/^# Finished Make data base/ \
						  {if ($$1 !~ "^[#.]") {print $$1}}' \
		| sort \
		| egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

.PHONY: runserver
runserver:
	$(call run_docker_backend, --network=host -e "OPENTA_VERSION=${OPENTA_VERSION}", python -u manage.py runserver 0.0.0.0:8000)

.PHONY: rqworker
rqworker:
	$(call run_docker_backend, --network=host, python -u manage.py rqworker)

.PHONY: migrate
migrate:
	$(call run_docker_backend, , python -u manage.py migrate)

.PHONY: reset_database
reset_database:
	make _reset_db
	make migrate
	make _fixtures

.PHONY: _reset_db
_reset_db:
	$(call run_docker_backend, , python -u manage.py reset_db)

.PHONY: _fixtures
_fixtures:
	$(call run_docker_backend, , python -u manage.py loaddata fixtures/auth.json)
	$(call run_docker_backend, , python -u manage.py loaddata fixtures/course.json)

.PHONY: test
test: frontend
	source django/env/bin/activate &&\
	cd django/backend &&\
	./runtests $(ARGS)

.PHONY: quick-test
quick-test:
	echo "Warning: Frontend not rebuilt, make sure you know what you are doing" &&\
	source django/env/bin/activate &&\
	cd django/backend &&\
	./runtests $(ARGS)

.PHONY: shell
shell:
	$(call run_docker_backend, , python -u manage.py shell)

.PHONY: build-docker
build-docker:
	docker build -f docker/Dockerfile.formatpy -t openta/formatpy docker/
	docker build -f ./docker/Dockerfile.backend -t openta/backend django/
	docker build -f ./docker/Dockerfile.frontend -t openta/frontend frontend/

.PHONY: format-python
format-python:
	@if [[ "$(shell docker images -q openta/formatpy 2> /dev/null)" == "" ]]; then\
		echo "Please run \"make build-docker\" first";\
	else\
		docker run --rm -u $(UID):$(GID) -v $(PWD)/django/backend:/code/django/backend openta/formatpy django/backend/;\
	fi;

.PHONY: frontend
frontend:
	$(info Revision: ${REVISION})
ifeq (, $(wildcard frontend/last_build/${REVISION}))
	$(call run_docker_frontend, -e "HOME=/tmp", npm install)
	$(call run_docker_frontend, , brunch build -p)
	$(call run_docker_backend, , python -u manage.py collectstatic --noinput --settings=backend.settings_base)
else
	$(info Frontend already built for the git revision ${REVISION})
endif

.PHONY: version
version:
	@echo ${COMMIT}

.PHONY: term
term:
	$(call run_docker_backend, --network=host, /bin/bash)

.PHONY: deploy-docker
deploy-docker:
	docker-compose -f docker/docker-compose.yml up

.PHONY: deploy-docker-setup
deploy-docker-setup:
	docker-compose -f docker/docker-compose.yml run web python manage.py migrate
	docker-compose -f docker/docker-compose.yml run web python manage.py loaddata fixtures/auth.json
	docker-compose -f docker/docker-compose.yml run web python manage.py loaddata fixtures/course.json

.PHONY: build-deploy-docker
build-deploy-docker: check-docker-repo-env build-docker frontend
	docker build -f docker_deploy/Dockerfile.nginx -t ${DOCKER_REPO}/nginx:${COMMIT} .
	docker build -f docker_deploy/Dockerfile.backendDeploy -t ${DOCKER_REPO}/openta:${COMMIT} .
	@echo "Push images with:"
	@echo "docker push ${DOCKER_REPO}/openta:${COMMIT} && docker push ${DOCKER_REPO}/nginx:${COMMIT}"

.PHONY: check-docker-repo-env
check-docker-repo-env:
	@if test "${DOCKER_REPO}" = "" ; then \
		echo "Run with: DOCKER_REPO=... make build-deploy-docker"; \
		echo "For example, if the images are located at reponame/openta:web"; \
		echo "DOCKER_REPO=reponame make build-deploy-docker"; \
		exit 1; \
	fi
