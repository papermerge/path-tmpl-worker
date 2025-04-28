import uuid

import jinja2
import redis
import logging

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
logger = logging.getLogger(__name__)
CHANNEL = "notifications"
redis_instance = redis.from_url(settings.papermerge__redis__url)


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENT)
def move_document(document_id: str):
    try:
        with Session() as db_session:
            message = api.move_document(db_session, uuid.UUID(document_id))
            ev = Event[DocumentMovedNotification](
                type=NOTIF_DOCUMENT_MOVED, payload=message
            )
            redis_instance.publish(CHANNEL, ev.model_dump_json())
    except TypeError as ex:
        logger.error(
            f"Error while moving document: {ex}. Double check path template string"
        )
    except jinja2.exceptions.TemplateSyntaxError as ex:
        logger.error(f"Error while moving document: {ex}. Path template syntax error")


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENTS)
def move_documents(document_type_id: str):
    """Move docs in bulk"""
    try:
        with Session() as db_session:
            payload = api.move_documents(db_session, uuid.UUID(document_type_id))
            ev = Event[DocumentsMovedNotification](
                type=NOTIF_DOCUMENTS_MOVED, payload=payload
            )
            redis_instance.publish(CHANNEL, ev.model_dump_json())
    except TypeError as ex:
        logger.error(
            f"Error while moving document: {ex}. Double check path template string"
        )
    except jinja2.exceptions.TemplateSyntaxError as ex:
        logger.error(f"Error while moving document: {ex}. Path template syntax error")
