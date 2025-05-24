from app.worker.celery_app import celery_app  # Import your Celery app instance


@celery_app.task(
    soft_time_limit=600,  # 10 min (Soft limit: raises exception if exceeded)
    time_limit=1200,      # 20 min (Hard limit: kills the task)
    bind=True,            # Allows access to `self` (task instance)
    max_retries=3,        # Retry 3 times on failure
    default_retry_delay=60,  # Wait 60s before retrying
)

def process_large_dataset(self, dataset_id):
    try:
        # Long-running task logic here
        ...
    except SoftTimeLimitExceeded:
        self.retry()  # Retry if soft limit is hit
