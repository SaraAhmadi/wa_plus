# app/worker/celery_app.py (or wherever your celery_app is defined)
from celery import Celery
from celery.schedules import crontab
from src.settings.config import settings

redis_url_str = str(settings.REDIS_URL)

celery_app = Celery(
    "waplus_tasks",
    broker=redis_url_str,
    backend=redis_url_str,
    include=[
        'app.worker.tasks' # Module where your tasks are defined
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC', # Example timezone
    enable_utc=True,
)

# Define your periodic tasks here if not using django-celery-beat
celery_app.conf.beat_schedule = {
    'add-every-30-seconds': {
        'task': 'app.worker.tasks.add', # Path to your task
        'schedule': 30.0, # In seconds
        'args': (16, 16)
    },
    'run-daily-report-at-midnight': {
        'task': 'app.worker.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0), # Runs daily at midnight
    },
}

# You would also need an app/worker/tasks.py file
# --- START OF EXAMPLE app/worker/tasks.py ---
# from .celery_app import celery_app
#
# @celery_app.task
# def add(x, y):
#     return x + y
#
# @celery_app.task
# def generate_daily_report():
#     print("Generating daily report...")
#     # Your report generation logic
#     return "Report generated"
# --- END OF EXAMPLE app/worker/tasks.py ---


if __name__ == '__main__':
    celery_app.start()