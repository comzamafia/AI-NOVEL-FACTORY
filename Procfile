# Procfile — Process definitions for Railway / Heroku-compatible platforms
#
# Railway uses railway.toml's startCommand for the web service.
# This Procfile documents all process types:
#
#   Web service →    use railway.toml startCommand
#   Worker service → set startCommand in Railway dashboard to the "worker" line
#   Beat service →   set startCommand in Railway dashboard to the "beat" line

web: python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile -
worker: celery -A config worker --loglevel=info --concurrency=4 --queues=default,ai_generation
beat: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
