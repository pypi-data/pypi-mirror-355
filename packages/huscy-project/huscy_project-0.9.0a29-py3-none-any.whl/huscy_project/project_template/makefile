# put #: in front of a command to provide help for it
#: show this help
help:
	@grep '#:' -A1 makefile | sed -rn '/^#:/ { N; s|^#: (.*)\n(.*):.*|\2 - \1|p }' | sort

#: run migrations for all applications
migrate:
	python manage.py migrate

#: create superuser
createsuperuser:
	python manage.py createsuperuser

#: start server
runserver:
	python manage.py runserver
