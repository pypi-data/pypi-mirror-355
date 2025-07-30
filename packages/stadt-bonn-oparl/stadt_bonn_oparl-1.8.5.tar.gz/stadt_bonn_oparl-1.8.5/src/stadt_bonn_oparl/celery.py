import logfire
from loguru import logger
from celery import Celery
from celery.schedules import crontab

from stadt_bonn_oparl.config import BROKER_URL
from stadt_bonn_oparl.logging import configure_logging

configure_logging(2)
logfire.instrument_celery()

logger.debug("Initializing Celery app with broker URL: %s", BROKER_URL)
app = Celery(
    "stadt_bonn_oparl",
    broker=BROKER_URL,
    result_backend="db+sqlite:///celery.sqlite",  # TODO: when deployed to openshift, use a proper database like PostgreSQL
    include=[
        "stadt_bonn_oparl.tasks.chromadb",
        "stadt_bonn_oparl.tasks.consultations",
        "stadt_bonn_oparl.tasks.convert",
        "stadt_bonn_oparl.tasks.download",
        "stadt_bonn_oparl.tasks.files",
        "stadt_bonn_oparl.tasks.meetings",
        "stadt_bonn_oparl.tasks.references",
    ],
)

app.conf.update(
    result_expires=3600,
    task_routes={
        "stadt_bonn_oparl.tasks.references.*": {"queue": "references"},
    },
    task_annotations={
        "stadt_bonn_oparl.tasks.references.resolve_reference_task": {
            "rate_limit": "100/m",  # Respect API rate limits
            "time_limit": 30,
            "soft_time_limit": 25,
        }
    },
    beat_schedule={
        # "check-missing-references": {
        #     "task": "stadt_bonn_oparl.tasks.references.check_and_resolve_missing_references",
        #     "schedule": 3600.0,  # Run every hour
        # },
        # "sync-meetings": {
        #    "task": "stadt_bonn_oparl.tasks.meetings.sync_meetings_task",
        #    "schedule": crontab(
        #        minute="*/15", hour="*", day_of_week=[1, 2, 3, 4, 5]
        #    ),  # Run every 15 minutes
        #    "args": (),
        #    "kwargs": {"max_pages": 2},
        # },
    },
)

app.conf.update(timezone="UTC")

if __name__ == "__main__":
    app.start()
