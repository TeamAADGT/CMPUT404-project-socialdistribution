release: python manage.py migrate
web: gunicorn social.wsgi
worker: python manage.py process_tasks