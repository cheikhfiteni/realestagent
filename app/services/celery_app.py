import uvloop
uvloop.install()

from celery import Celery
from celery.signals import task_failure
from app.config import REDIS_URL

celery = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)

celery.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    imports=['app.logic'],
    worker_pool='solo',
)

# This is still useful for other tasks, but we explicitly import logic
celery.autodiscover_tasks(['app'])

@task_failure.connect
def handle_task_failure(task_id=None, exception=None, **kwargs):
    print(f"Task {task_id} failed: {exception}")