import uuid
from datetime import datetime
from pathlib import PurePath
from sqlalchemy import text, select, insert, update
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from path_tmpl_worker import models
from path_tmpl_worker.template import get_evaluated_path
from path_tmpl_worker.constants import INCOMING_DATE_FORMAT, CTYPE_FOLDER
from path_tmpl_worker.db.orm import (
    Document,
    CustomField,
    CustomFieldValue,
    User,
    Folder,
    DocumentType,
)


def get_user(session: Session, document_id: uuid.UUID) -> User:
    stmt = select(User).join(Document).where(Document.id == document_id)
    return session.execute(stmt).scalars().one()


def get_path_template(session: Session, document_id: uuid.UUID) -> str:
    stmt = (
        select(DocumentType.path_template)
        .join(Document)
        .where(Document.id == document_id)
    )
    path_template = session.execute(stmt).scalars().one_or_none()

    return path_template


def get_doc_cfv(session: Session, document_id: uuid.UUID) -> list[models.CFV]:
    stmt = """ 
        SELECT
            doc.basetreenode_ptr_id AS doc_id,
            doc.document_type_id,
            cf.cf_id AS cf_id,
            cf.cf_name,
            cf.cf_type AS cf_type,
            cfv.id AS cfv_id,
            CASE
                WHEN(cf.cf_type = 'monetary') THEN cfv.value_monetary
                WHEN(cf.cf_type = 'text') THEN cfv.value_text
                WHEN(cf.cf_type = 'date') THEN cfv.value_date
                WHEN(cf.cf_type = 'boolean') THEN cfv.value_boolean
            END AS cf_value
        FROM core_document AS doc
        JOIN document_type_custom_field AS dtcf ON dtcf.document_type_id = doc.document_type_id
        JOIN(
            SELECT
                sub_cf1.id AS cf_id,
                sub_cf1.name AS cf_name,
                sub_cf1.type AS cf_type,
                sub_cf1.extra_data AS cf_extra_data
            FROM core_document AS sub_doc1
            JOIN document_type_custom_field AS sub_dtcf1
                ON sub_dtcf1.document_type_id = sub_doc1.document_type_id
            JOIN custom_fields AS sub_cf1
                ON sub_cf1.id = sub_dtcf1.custom_field_id
            WHERE sub_doc1.basetreenode_ptr_id = :document_id
        ) AS cf ON cf.cf_id = dtcf.custom_field_id
        LEFT OUTER JOIN custom_field_values AS cfv
            ON cfv.field_id = cf.cf_id AND cfv.document_id = :document_id
    WHERE
        doc.basetreenode_ptr_id = :document_id
    """
    custom_fields = []
    str_doc_id = str(document_id).replace("-", "")
    for row in session.execute(text(stmt), {"document_id": str_doc_id}):
        if row.cf_type == "date":
            value = str2date(row.cf_value)
        else:
            value = row.cf_value
        custom_fields.append(
            models.CFV(
                document_id=row.doc_id,
                document_type_id=row.document_type_id,
                custom_field_id=row.cf_id,
                name=row.cf_name,
                type=row.cf_type,
                custom_field_value_id=row.cfv_id,
                value=value,
            )
        )

    return custom_fields


def get_document(session: Session, document_id: uuid.UUID) -> Document:
    stmt = select(Document).where(Document.id == document_id)

    return session.execute(stmt).scalars().one()


def get_doc_ctx(session: Session, document_id: uuid.UUID) -> models.DocumentContext:
    cf = get_doc_cfv(session, document_id)
    custom_fields = [models.CField(name=i.name, value=i.value) for i in cf]
    doc = get_document(session, document_id)

    return models.DocumentContext(
        title=doc.title, id=document_id, custom_fields=custom_fields
    )


def str2date(value: str | None) -> Optional[datetime.date]:
    """Convert incoming user string to datetime.date"""
    # 10 = 4 Y chars +  1 "-" char + 2 M chars + 1 "-" char + 2 D chars
    if value is None:
        return None

    DATE_LEN = 10
    stripped_value = value.strip()
    if len(stripped_value) == 0:
        return None

    if len(stripped_value) < DATE_LEN and len(stripped_value) > 0:
        raise ValueError(
            f"{stripped_value} expected to have at least {DATE_LEN} characters"
        )

    return datetime.strptime(
        value[:DATE_LEN],
        INCOMING_DATE_FORMAT,
    ).date()


def update_doc_cfv(
    session: Session,
    document_id: uuid.UUID,
    custom_fields: dict,
):
    """
    Update document's custom field values
    """
    items = get_doc_cfv(session, document_id=document_id)
    insert_values = []
    update_values = []

    stmt = (
        select(CustomField.name)
        .select_from(CustomFieldValue)
        .join(CustomField)
        .where(CustomFieldValue.document_id == document_id)
    )
    existing_cf_name = [row[0] for row in session.execute(stmt).all()]

    for item in items:
        if item.name not in custom_fields.keys():
            continue

        if item.name not in existing_cf_name:
            # prepare insert values
            v = dict(
                id=uuid.uuid4(),
                document_id=item.document_id,
                field_id=item.custom_field_id,
            )
            if item.type.value == "date":
                v[f"value_{item.type.value}"] = str2date(custom_fields[item.name])
            else:
                v[f"value_{item.type.value}"] = custom_fields[item.name]
            insert_values.append(v)
        else:
            # prepare update values
            v = dict(id=item.custom_field_value_id)
            if item.type == "date":
                v[f"value_{item.type.value}"] = str2date(custom_fields[item.name])
            else:
                v[f"value_{item.type.value}"] = custom_fields[item.name]
            update_values.append(v)

    if len(insert_values) > 0:
        session.execute(insert(CustomFieldValue), insert_values)

    if len(update_values) > 0:
        session.execute(update(CustomFieldValue), update_values)

    session.commit()

    return items


def get_user_home(session: Session, user_id: uuid.UUID) -> Folder:
    stmt = select(User).where(User.id == user_id)
    user = session.execute(stmt).scalars().one()
    return user.home_folder


def mkdir_node(session: Session, path: PurePath, parent: Folder, user_id: uuid.UUID):
    if path in [PurePath("."), PurePath("/"), PurePath("home")]:
        return parent

    if path.name in ["home", ".home"]:
        return parent

    folder = (
        session.execute(
            select(Folder).where(
                Folder.parent_id == parent.id,
                Folder.title == path.name,
                Folder.user_id == user_id,
            )
        )
        .scalars()
        .one_or_none()
    )

    if folder is None:
        folder = Folder(
            id=uuid.uuid4(),
            title=path.name,
            parent_id=parent.id,
            user_id=user_id,
            lang="en",
            ctype=CTYPE_FOLDER,
        )
        session.add(folder)
        session.commit()

    return folder


def mkdir(session: Session, path: PurePath, user_id: uuid.UUID) -> Folder:
    """makes all node folders specified in path

    It is assumed that Top-most folder is user's `/home/` folder.
    If path does not start with /home/
    it will implicitly assume '/home/' already exists and put
    created nodes under that folder.
    E.g.

    mkdir('/My Documents/Here/invoice.pdf', 'uuid1') will
    create folders 'My Documents` and put it in uuid1 user's home folder i.e.
    existing /home/ folder belonging to user with uuid1.
    Then it will create folder `Here` and put it under /home/My Documents/
    of the user `uuid1`.

    If path is not absolute, it will be considered relative to user's home folder
    """
    parent = get_user_home(session, user_id)

    for node in reversed(PurePath(path).parents):
        parent = mkdir_node(session, node, parent=parent, user_id=user_id)

    return parent


def mkdir_target(session: Session, document_id: uuid.UUID) -> Tuple[str, Folder]:
    doc = get_doc_ctx(session, document_id)
    path_template = get_path_template(session, document_id)
    user = get_user(session, document_id)
    ev_path = get_evaluated_path(doc, path_template)
    target_folder = mkdir(session, path=PurePath(ev_path), user_id=user.id)

    return ev_path, target_folder
