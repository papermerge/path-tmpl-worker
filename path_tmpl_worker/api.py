import uuid
from pathlib import PurePath

from sqlalchemy.orm import Session
from path_tmpl_worker import db


def move_document(db_session: Session, document_id: uuid.UUID):
    document = db.get_document(db_session, document_id)
    ev_path, target_parent = db.mkdir_target(db_session, document_id)

    document.title = PurePath(ev_path).name
    document.parent_id = target_parent.id

    db_session.commit()
