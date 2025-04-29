import uuid
from datetime import datetime
from pathlib import PurePath
from sqlalchemy import select, insert, update, func, Select, VARCHAR, case
from sqlalchemy.orm import Session, aliased
from typing import Optional, Tuple

from pathtmpl import get_evaluated_path, DocumentContext, CField

from path_tmpl_worker.ordered_document_cfv import OrderedDocumentCFV
from path_tmpl_worker import models
from path_tmpl_worker.constants import INCOMING_DATE_FORMAT, CTYPE_FOLDER
from path_tmpl_worker.db.orm import (
    Document,
    CustomField,
    CustomFieldValue,
    User,
    Folder,
    DocumentType,
    DocumentTypeCustomField,
    Group,
)


# len(2024-11-02) + 1
DATE_LEN = 11


def document_type_cf_count(session: Session, document_type_id: uuid.UUID):
    """count number of custom fields associated to document type"""
    stmt = select(DocumentType).where(DocumentType.id == document_type_id)
    dtype = session.scalars(stmt).one()
    return len(dtype.custom_fields)


def get_docs_count_by_type(session: Session, type_id: uuid.UUID):
    """Returns number of documents of specific document type"""
    stmt = (
        select(func.count())
        .select_from(Document)
        .where(Document.document_type_id == type_id)
    )

    return session.scalars(stmt).one()


def _select_cf() -> Select:
    stmt = (
        select(
            CustomField.id,
            CustomField.name,
            CustomField.type,
            CustomField.extra_data,
        )
        .select_from(Document)
        .join(
            DocumentTypeCustomField,
            DocumentTypeCustomField.document_type_id == Document.document_type_id,
        )
        .join(
            CustomField,
            CustomField.id == DocumentTypeCustomField.custom_field_id,
        )
    )

    return stmt


def select_cf_by_document_type(document_type_id: uuid.UUID) -> Select:
    """Returns SqlAlchemy selector for document custom fields"""
    stmt = (
        _select_cf()
        .where(Document.document_type_id == document_type_id)
        .group_by(CustomField.id)
    )

    return stmt


def select_docs_by_type(
    document_type_id: uuid.UUID,
    limit: int,
    offset: int,
) -> Select:
    assoc = aliased(DocumentTypeCustomField, name="assoc")
    doc = aliased(Document, name="doc")
    cf = select_cf_by_document_type(document_type_id).subquery("cf")
    cfv = aliased(CustomFieldValue, name="cfv")

    base_stmt = (
        select(
            doc.title,
            doc.id.label("doc_id"),
            doc.document_type_id.label("document_type_id"),
            doc.parent_id,
            cf.c.name.label("cf_name"),
            cf.c.type.label("cf_type"),
            case(
                (cf.c.type == "monetary", func.cast(cfv.value_monetary, VARCHAR)),
                (cf.c.type == "text", func.cast(cfv.value_text, VARCHAR)),
                (
                    cf.c.type == "date",
                    func.substr(func.cast(cfv.value_date, VARCHAR), 0, DATE_LEN),
                ),
                (cf.c.type == "boolean", func.cast(cfv.value_boolean, VARCHAR)),
            ).label("cf_value"),
        )
        .select_from(doc)
        .join(assoc, assoc.document_type_id == doc.document_type_id)
        .join(cf, cf.c.id == assoc.custom_field_id)
        .join(
            cfv, (cfv.field_id == cf.c.id) & (cfv.document_id == doc.id), isouter=True
        )
    )

    stmt = base_stmt.where(doc.document_type_id == document_type_id)
    return stmt.limit(limit).offset(offset)


def get_docs_by_type_no_cf(
    session: Session,
    type_id: uuid.UUID,
    limit: int,
    offset: int,
) -> list[models.DocumentCFV]:
    """Return all documents of specific type (with their empty custom fields)

    This method works correctly only in case document type does
    not have custom fields
    """
    stmt = (
        select(Document)
        .where(Document.document_type_id == type_id)
        .limit(limit)
        .offset(offset)
    )

    results = []

    for doc in session.execute(stmt).scalars():
        item = models.DocumentCFV(
            id=doc.id,
            title=doc.title,
            parent_id=doc.parent_id,
            document_type_id=type_id,
            custom_fields=[],
        )
        results.append(item)

    return results


def get_docs_by_type(
    session: Session,
    document_type_id: uuid.UUID,
    page_number: int = 1,
    page_size: int = 300,
) -> list[models.DocumentCFV]:

    cf_count = document_type_cf_count(session, document_type_id=document_type_id)

    if cf_count == 0:
        return get_docs_by_type_no_cf(
            session,
            type_id=document_type_id,
            limit=page_size,
            offset=(page_number - 1) * page_size,
        )

    stmt = select_docs_by_type(
        document_type_id=document_type_id,
        limit=cf_count * page_size,
        offset=cf_count * (page_number - 1) * page_size,
    )
    rows = session.execute(stmt)

    ordered_doc_cfvs = OrderedDocumentCFV()
    for row in rows:
        entry = models.DocumentCFVRow(
            title=row.title,
            doc_id=row.doc_id,
            parent_id=row.parent_id,
            document_type_id=row.document_type_id,
            cf_name=row.cf_name,
            cf_type=row.cf_type,
            cf_value=row.cf_value,
        )
        ordered_doc_cfvs.add(entry)

    return list(ordered_doc_cfvs)


def get_document_type(session: Session, document_type_id: uuid.UUID) -> DocumentType:
    stmt = select(DocumentType).where(DocumentType.id == document_type_id)
    db_item = session.scalars(stmt).unique().one()
    return db_item


def get_path_template(session: Session, document_id: uuid.UUID) -> str:
    stmt = (
        select(DocumentType.path_template)
        .join(Document)
        .where(Document.id == document_id)
    )
    path_template = session.execute(stmt).scalars().one_or_none()

    return path_template


def select_cf_by_document_id(document_id: uuid.UUID) -> Select:
    stmt = (
        select(
            CustomField.id, CustomField.name, CustomField.type, CustomField.extra_data
        )
        .select_from(Document)
        .join(
            DocumentTypeCustomField,
            DocumentTypeCustomField.document_type_id == Document.document_type_id,
        )
        .join(CustomField, CustomField.id == DocumentTypeCustomField.custom_field_id)
    ).where(Document.id == document_id)

    return stmt


def select_doc_cfv(document_id: uuid.UUID) -> Select:
    """Returns SqlAlchemy selector for document custom field values"""
    cf = select_cf_by_document_id(document_id).subquery("cf")
    cfv = aliased(CustomFieldValue, name="cfv")
    assoc = aliased(DocumentTypeCustomField, name="assoc")
    doc = aliased(Document, name="doc")

    stmt = (
        select(
            doc.id.label("doc_id"),
            doc.document_type_id,
            cf.c.name.label("cf_name"),
            cf.c.extra_data.label("cf_extra_data"),
            cf.c.type.label("cf_type"),
            cf.c.id.label("cf_id"),
            cfv.id.label("cfv_id"),
            case(
                (cf.c.type == "monetary", func.cast(cfv.value_monetary, VARCHAR)),
                (cf.c.type == "text", func.cast(cfv.value_text, VARCHAR)),
                (
                    cf.c.type == "date",
                    func.substr(func.cast(cfv.value_date, VARCHAR), 0, DATE_LEN),
                ),
                (cf.c.type == "boolean", func.cast(cfv.value_boolean, VARCHAR)),
            ).label("cf_value"),
        )
        .select_from(doc)
        .join(assoc, assoc.document_type_id == doc.document_type_id)
        .join(cf, cf.c.id == assoc.custom_field_id)
        .join(
            cfv,
            (cfv.field_id == cf.c.id) & (cfv.document_id == document_id),
            isouter=True,
        )
        .where(doc.id == document_id)
    )

    return stmt


def get_doc_cfv(session: Session, document_id: uuid.UUID) -> list[models.CFV]:
    stmt = select_doc_cfv(document_id)
    result = []
    for row in session.execute(stmt):
        if row.cf_type == "date":
            value = str2date(row.cf_value)
        else:
            value = row.cf_value

        result.append(
            models.CFV(
                document_id=row.doc_id,
                document_type_id=row.document_type_id,
                custom_field_id=row.cf_id,
                name=row.cf_name,
                type=row.cf_type,
                extra_data=row.cf_extra_data,
                custom_field_value_id=row.cfv_id,
                value=value,
            )
        )

    return result


def get_document(session: Session, document_id: uuid.UUID) -> Document:
    stmt = select(Document).where(Document.id == document_id)

    return session.execute(stmt).scalars().one()


def get_doc_ctx(session: Session, document_id: uuid.UUID) -> DocumentContext:
    cf = get_doc_cfv(session, document_id)
    custom_fields = [CField(name=i.name, value=i.value) for i in cf]
    doc = get_document(session, document_id)

    return DocumentContext(title=doc.title, id=document_id, custom_fields=custom_fields)


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


def get_home(
    session: Session,
    user_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
) -> Folder:

    if group_id is not None:
        stmt = select(Group).where(Group.id == group_id)
        group = session.execute(stmt).scalars().one()
        home_id = group.home_folder_id
    else:
        stmt = select(User).where(User.id == user_id)
        user = session.execute(stmt).scalars().one()
        home_id = user.home_folder_id

    stmt = select(Folder).where(Folder.id == home_id)
    home = session.execute(stmt).scalars().one()

    return home


def mkdir_node(
    session: Session,
    path: PurePath,
    parent: Folder,
    user_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
):
    if path in [PurePath("."), PurePath("/"), PurePath("home")]:
        return parent

    if path.name in ["home", ".home"]:
        return parent

    folder = (
        session.execute(
            select(Folder).where(
                Folder.parent_id == parent.id,
                Folder.title == path.name,
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
            group_id=group_id,
            lang="en",
            ctype=CTYPE_FOLDER,
        )
        session.add(folder)
        session.commit()

    return folder


def mkdir(
    session: Session,
    path: str,
    user_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
) -> Folder:
    """makes all node folders specified in path

    It is assumed that Top-most folder is `/home/` folder.
    If path does not start with /home/
    it will implicitly assume '/home/' already exists and put
    created nodes under that folder.
    E.g.

    mkdir('/My Documents/Here/invoice.pdf', 'uuid1') will
    create folders 'My Documents` and put it in uuid1 user (or group, depending
    on who owns the document) home folder i.e.
    existing /home/ folder belonging to user/group with uuid1.
    Then it will create folder `Here` and put it under /home/My Documents/
    of the user/group `uuid1`.

    If path is not absolute, it will be considered relative to user/group's home folder
    """

    parent = get_home(session, user_id=user_id, group_id=group_id)

    stripped_path = path.strip()
    if stripped_path.endswith("/"):
        # Last part of the path is a folder, include it as parent
        parents = [PurePath(stripped_path), *PurePath(stripped_path).parents]
    else:
        parents = PurePath(stripped_path).parents

    for node in reversed(parents):
        parent = mkdir_node(
            session, node, parent=parent, user_id=user_id, group_id=group_id
        )

    return parent


def mkdir_target(session: Session, document_id: uuid.UUID) -> Tuple[str, Folder]:
    doc = get_doc_ctx(session, document_id)
    path_template = get_path_template(session, document_id)
    ev_path = get_evaluated_path(doc, path_template)
    stmt = select(Document).where(Document.id == document_id)
    doc = session.execute(stmt).scalars().one()
    target_folder = mkdir(
        session, path=ev_path, user_id=doc.user_id, group_id=doc.group_id
    )

    return ev_path, target_folder
