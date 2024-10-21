import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session
from path_tmpl_worker import db
from pathtmpl import DocumentContext, CField, get_evaluated_path

from path_tmpl_worker.db.api import get_user
from path_tmpl_worker.db.orm import Document
from path_tmpl_worker.models import DocumentCFV, BulkUpdate

PAGE_SIZE = 1000


def move_document(db_session: Session, document_id: uuid.UUID):
    document = db.get_document(db_session, document_id)
    ev_path, target_parent = db.mkdir_target(db_session, document_id)

    document.title = ev_path.name
    document.parent_id = target_parent.id

    db_session.commit()


def move_documents(db_session: Session, document_type_id: uuid.UUID):
    dtype = db.get_document_type(db_session, document_type_id)
    total_count = db.get_docs_count_by_type(db_session, document_type_id)
    page_size = min(PAGE_SIZE, total_count)
    number_of_pages = int(total_count / page_size) + 1

    for page_number in range(1, number_of_pages + 1):
        doc_cfvs: list[DocumentCFV] = db.get_docs_by_type(
            db_session, document_type_id, page_number=page_number, page_size=page_size
        )
        updates = []
        for doc_cfv in doc_cfvs:
            custom_fields = [
                CField(name=cf[0], value=cf[1]) for cf in doc_cfv.custom_fields
            ]
            ctx = DocumentContext(
                id=doc_cfv.id, title=doc_cfv.title, custom_fields=custom_fields
            )
            ev_path = get_evaluated_path(ctx, dtype.path_template)
            updates.append(BulkUpdate(document_id=ctx.id, ev_path=ev_path))

        bulk_apply(db_session, updates)
    db_session.commit()


def bulk_apply(db_session: Session, updates: list[BulkUpdate]):
    if len(updates) < 1:
        return

    user = get_user(db_session, updates[0].document_id)
    target_folder = db.mkdir(db_session, updates[0].ev_path, user.id)
    update_values = []
    for item in updates:
        v = {
            "id": item.document_id,
            "parent_id": target_folder.id,
            "title": item.ev_path.name,
        }
        update_values.append(v)

    db_session.execute(update(Document), update_values)
