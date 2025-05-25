from .celery_app import celery_app # Assuming celery_app is in celery_app.py
# If celery_app is in worker.py: from . import celery_app
# Or from app.worker.celery_app import celery_app if running from project root context


@celery_app.task(name="add_example") # Explicitly naming is good practice
def add(x: int, y: int) -> int:
    result = x + y
    print(f"Task 'add_example': {x} + {y} = {result}")
    return result


@celery_app.task(name="generate_daily_report_example")
def generate_daily_report():
    report_content = f"Daily report generated at {datetime.now()}"
    print(f"Task 'generate_daily_report_example': {report_content}")
    # In a real scenario, this would do significant work
    return report_content

# Add any other tasks your application needs here.
# For example, a task for the data ingestion pipeline:
# @celery_app.task(name="run_data_ingestion")
# def run_data_ingestion_task(file_path: str, file_type: str, config: dict):
#     from app.data_ingestion.pipeline import IngestionPipeline
#     from app.database.session import AsyncSessionFactory # For standalone task session
#     import asyncio
#
#     async def _run():
#         async with AsyncSessionFactory() as session:
#             pipeline = IngestionPipeline(db_session=session, config=config.get("pipeline_config"))
#             await pipeline.run_for_file(
#                 file_path=file_path,
#                 file_type=file_type,
#                 target_model_name=config.get("target_model_name"), # Need to map name to class
#                 ingestion_config=config.get("ingestion_config")
#             )
#     asyncio.run(_run())
#     return f"Data ingestion task for {file_path} completed."

# Make sure to import datetime if you use it
from datetime import datetime