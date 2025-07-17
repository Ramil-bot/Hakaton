import os
from celery import Celery

# Укажите имя вашего Django-проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')  # Имя должно совпадать с папкой проекта
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()