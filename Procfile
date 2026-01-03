web: daphne HeroHoursRemake.asgi --log-file -
heroku run python manage.py collectstatic
heroku run python manage.py makemigrations
heroku run python manage.py migrate
