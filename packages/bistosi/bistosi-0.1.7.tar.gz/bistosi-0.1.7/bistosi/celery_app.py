import os
import dotenv
dotenv.load_dotenv("../.env")
from celery import Celery

REDIS_URL = f"redis://:{os.getenv('BISTOSI_REDIS_PASS')}@{os.getenv('BISTOSI_REDIS_HOST')}:{os.getenv('BISTOSI_REDIS_PORT')}/1"
app = Celery(
    'apply_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# app.conf.timezone = 'UTC'
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()
