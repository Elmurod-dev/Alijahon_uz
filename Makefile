mig:
	./manage.py makemigrations
	./manage.py migrate

load:
	./manage.py loaddata category_fixture.json
	./manage.py loaddata regions_fixture.json
	./manage.py loaddata districts_fixture.json

user:
	./manage.py createsuperuser
