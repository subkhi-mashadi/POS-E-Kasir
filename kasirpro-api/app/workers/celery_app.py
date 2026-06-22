from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "kasirpro",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.sync_worker",
        "app.workers.report_worker",
        "app.workers.notification_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    beat_schedule={
        "check-low-stock-every-hour": {
            "task": "notification.check_low_stock",
            "schedule": 3600.0,  # tiap jam
            "args": ["public", "Cabang Utama"],
        },
        "daily-report-midnight": {
            "task": "notification.daily_report",
            "schedule": 86400.0,  # tiap hari
        },
    },
)
