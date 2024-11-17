import uuid
import redis

from celery import shared_task

from path_tmpl_worker.constants import NOTIF_DOCUMENT_MOVED, NOTIF_DOCUMENTS_MOVED
from path_tmpl_worker.db.engine import Session
from path_tmpl_worker import api
from path_tmpl_worker import constants, config
from path_tmpl_worker.models import (
    Event,
    DocumentMovedNotification,
    DocumentsMovedNotification,
)

settings = config.get_settings()

CHANNEL = "notifications"
redis_instance = redis.from_url(settings.papermerge__redis__url)


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENT)
def move_document(document_id: str, user_id: str):
    with Session() as db_session:
        message = api.move_document(
            db_session, uuid.UUID(document_id), uuid.UUID(user_id)
        )
        ev = Event[DocumentMovedNotification](
            type=NOTIF_DOCUMENT_MOVED, payload=message
        )
        redis_instance.publish(CHANNEL, ev.model_dump_json())


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENTS)
def move_documents(document_type_id: str, user_id: str):
    """Move docs in bulk"""
    with Session() as db_session:
        payload = api.move_documents(
            db_session, uuid.UUID(document_type_id), uuid.UUID(user_id)
        )
        ev = Event[DocumentsMovedNotification](
            type=NOTIF_DOCUMENTS_MOVED, payload=payload
        )
        redis_instance.publish(CHANNEL, ev.model_dump_json())
