# app/worker/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "waplus",
    broker=str(settings.REDIS_URL),  # e.g. redis://redis:6379/0
    backend=str(settings.REDIS_URL).rsplit('/', 1)[0] + "/1"  # Different DB for results
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Add your timeout settings here along with other conf settings
    task_soft_time_limit=300,  # 5 minutes (soft limit - raises SoftTimeLimitExceeded)
    task_time_limit=600,  # 10 minutes (hard limit - kills the task)

    # Other configuration options...
    task_default_queue="default",
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)


celery_app.conf.beat_scheduler = "redbeat.RedBeatScheduler"
celery_app.conf.redbeat_redis_url = "redis://redis:6379/3"  # Use DB 3