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
	source django/env/bin/activate &&\
	cd django/backend &&\
	python manage.py runserver

.PHONY: rqworker
rqworker:
	source django/env/bin/activate &&\
	cd django/backend &&\
	python manage.py rqworker

.PHONY: migrate
migrate:
	source django/env/bin/activate; \
	python django/backend/manage.py migrate ;\

.PHONY: reset_database
reset_database:
	make _reset_db
	make migrate
	make _fixtures

.PHONY: _reset_db
_reset_db:
	source django/env/bin/activate; \
	python django/backend/manage.py reset_db ;\

.PHONY: _fixtures
_fixtures:
	source django/env/bin/activate; \
	python django/backend/manage.py loaddata django/backend/fixtures/auth.json ;\
	python django/backend/manage.py loaddata django/backend/fixtures/course.json ;\

.PHONY: frontend
frontend:
	cd frontend; \
	brunch watch; \

.PHONY: test
test:
	source django/env/bin/activate &&\
	cd django/backend &&\
	./runtests

.PHONY: shell
shell:
	source django/env/bin/activate &&\
	cd django/backend &&\
	python manage.py shell
