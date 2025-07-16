from pathlib import PurePath
import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session
from path_tmpl_worker import db
from pathtmpl import DocumentContext, CField, get_evaluated_path

from path_tmpl_worker.db.orm import Document
from path_tmpl_worker.models import (
    DocumentCFV,
    BulkUpdate,
    DocumentsMovedNotification,
    DocumentMovedNotification,
)

PAGE_SIZE = 1000


def move_document(
    db_session: Session, document_id: uuid.UUID
) -> DocumentMovedNotification:
    """Move document

    Evaluate new document path (based on path template of the associated
    document type) and (maybe) move document to the new location.
    Document may eventually get new title.
    """
    document = db.get_document(db_session, document_id)
    source_folder_id = document.parent_id
    old_document_title = document.title
    ev_path, target_parent = db.mkdir_target(db_session, document_id)

    stripped_ev_path = ev_path.strip()
    if stripped_ev_path.endswith("/"):
        # title does not change
        new_document_title = document.title
    else:
        document.title = PurePath(stripped_ev_path).name
        new_document_title = PurePath(stripped_ev_path).name

    document.parent_id = target_parent.id

    db_session.commit()
    return DocumentMovedNotification(
        document_id=document_id,
        old_document_title=old_document_title,
        new_document_title=new_document_title,
        source_folder_id=source_folder_id,
        target_folder_id=target_parent.id,
    )


def move_documents(
    db_session: Session, document_type_id: uuid.UUID
) -> DocumentsMovedNotification:
    """Move documents in bulk

    Affects all documents with type id = `document_type_id`
    For each document of given type evaluate new document path (based on path
        template of the associated document type)
    And then apply bulk update of the new docs.parent_id and docs.title
    (both paren_id and title may change depending on the evaluated path)
    """
    dtype = db.get_document_type(db_session, document_type_id)
    total_count = db.get_docs_count_by_type(db_session, document_type_id)
    # May happen that `total_count == 0`
    page_size = min(PAGE_SIZE, total_count) or PAGE_SIZE
    # to avoid `page_size` == 0 we do: page_size = min(...) or PAGE_SIZE
    number_of_pages = int(total_count / page_size) + 1
    total_moved = 0
    source_folder_ids = set()
    target_folder_ids = set()

    for page_number in range(1, number_of_pages + 1):
        doc_cfvs: list[DocumentCFV] = db.get_docs_by_type(
            db_session,
            document_type_id,
            page_number=page_number,
            page_size=page_size,
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
            source_folder_ids.add(doc_cfv.parent_id)
            updates.append(
                BulkUpdate(document_id=ctx.id, ev_path=ev_path, title=ctx.title)
            )

        target_folder_ids.update(
            apply_updates(
                db_session, updates, user_id=dtype.user_id, group_id=dtype.group_id
            )
        )
        total_moved += len(updates)

    db_session.commit()
    return DocumentsMovedNotification(
        source_folder_ids=source_folder_ids,
        target_folder_ids=target_folder_ids,
        count=total_moved,
        document_type_name=dtype.name,
        document_type_id=dtype.id,
    )


def apply_updates(
    db_session: Session,
    updates: list[BulkUpdate],
    user_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
) -> list[uuid.UUID]:
    if len(updates) < 1:
        return []

    target_folder_ids = []
    update_values = []
    for item in updates:
        stripped_ev_path = item.ev_path.strip()
        target_folder = db.mkdir(
            db_session, stripped_ev_path, user_id=user_id, group_id=group_id
        )
        if stripped_ev_path.endswith("/"):
            v = {
                "id": item.document_id,
                "parent_id": target_folder.id,
                "title": item.title,
            }
        else:
            v = {
                "id": item.document_id,
                "parent_id": target_folder.id,
                "title": PurePath(stripped_ev_path).name,
            }
        update_values.append(v)
        target_folder_ids.append(target_folder.id)

    db_session.execute(update(Document), update_values)

    return target_folder_ids
