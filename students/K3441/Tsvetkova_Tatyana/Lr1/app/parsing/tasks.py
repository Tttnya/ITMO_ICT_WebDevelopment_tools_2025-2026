from ..celery_app import celery_app
from .service import parse_and_save


@celery_app.task(name="app.parsing.tasks.parse_url_task")
def parse_url_task(url: str) -> dict:
    page = parse_and_save(url=url, approach="celery")
    return {
        "id": page.id,
        "url": page.url,
        "title": page.title,
        "approach": page.approach,
        "created_at": page.created_at.isoformat(),
    }
