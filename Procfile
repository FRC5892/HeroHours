web: daphne HeroHoursRemake.asgi:application --port 80 --bind 0.0.0.0
heroku run python manage.py collectstatic
heroku run python manage.py makemigrations
heroku run python manage.py migrate
