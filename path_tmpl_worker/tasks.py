import uuid

from celery import shared_task
from path_tmpl_worker.db import get_db
from path_tmpl_worker import api
from path_tmpl_worker import constants


@shared_task(name=constants.PATH_TMPL_MOVE_DOCUMENT)
def move_document(document_id: str):
    with get_db() as session:
        api.move_document(session, uuid.UUID(document_id))
