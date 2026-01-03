web: daphne HeroHoursRemake.asgi:application --port $PORT --bind 0.0.0.0 --proxy-headers
heroku run python manage.py collectstatic
heroku run python manage.py makemigrations
heroku run python manage.py migrate
