import uuid

import jinja2
import redis
import logging

from celery import shared_task

from path_tmpl_worker.db.engine import Session
from path_tmpl_worker import db
from path_tmpl_worker import constants, config

settings = config.get_settings()
logger = logging.getLogger(__name__)
CHANNEL = "notifications"
redis_instance = redis.from_url(settings.papermerge__redis__url)


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENT)
def move_document(document_id: str):
    try:
        with Session() as db_session:
            db.move_document(db_session, uuid.UUID(document_id))
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
            api.move_documents(db_session, uuid.UUID(document_type_id))
    except TypeError as ex:
        logger.error(
            f"Error while moving document: {ex}. Double check path template string"
        )
    except jinja2.exceptions.TemplateSyntaxError as ex:
        logger.error(f"Error while moving document: {ex}. Path template syntax error")
