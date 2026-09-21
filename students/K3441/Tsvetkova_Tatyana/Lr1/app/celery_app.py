"""Конфигурация Celery: Redis как брокер и хранилище результатов
(лабораторная работа №3, подзадача 3)."""
import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery("bookcrossing", broker=broker_url, backend=result_backend)
celery_app.conf.task_track_started = True
celery_app.autodiscover_tasks(["app.parsing"])
