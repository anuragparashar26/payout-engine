import os

from celery import Celery
from celery.schedules import schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "reap-stuck-payouts": {
        "task": "payouts.tasks.reap_stuck_payouts",
        "schedule": schedule(run_every=30.0),
    }
}
