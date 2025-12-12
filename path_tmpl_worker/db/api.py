import uuid
from pathlib import PurePath
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Tuple

from pathtmpl import get_evaluated_path, Context

from path_tmpl_worker.db.orm import (
    Document,
    User,
    Folder,
    DocumentType,
    Group,
    DocumentVersion,
    Ownership,
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


def get_document_context(session: Session, document_id: uuid.UUID) -> Context:
    """Build context for path template evaluation.

    Fetches document and its latest version in a single query.
    """
    latest_version_subq = (
        select(DocumentVersion.id)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.number.desc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = (
        select(Document, DocumentVersion)
        .join(DocumentVersion, DocumentVersion.document_id == Document.id)
        .where(Document.id == document_id)
        .where(DocumentVersion.id == latest_version_subq)
    )

    doc, latest_version = session.execute(stmt).one()

    return Context(
        id=document_id,
        title=doc.title,
        file_name=latest_version.file_name,
        category=doc.document_type.name if doc.document_type else "",
        year=latest_version.created_at.year,
        month=latest_version.created_at.month,
        day=latest_version.created_at.day,
    )


def get_node_ownership(session: Session, node_id: uuid.UUID) -> Ownership:
    """Get ownership record for a node (document or folder)."""
    stmt = select(Ownership).where(
        Ownership.resource_type == "node",
        Ownership.resource_id == node_id,
    )
    return session.execute(stmt).scalars().one()


def get_owner_home_folder(session: Session, ownership: Ownership) -> Folder:
    """Get home folder for an owner (user or group)."""
    if ownership.owner_type == "group":
        stmt = select(Group).where(Group.id == ownership.owner_id)
        owner = session.execute(stmt).scalars().one()
    else:
        stmt = select(User).where(User.id == ownership.owner_id)
        owner = session.execute(stmt).scalars().one()

    stmt = select(Folder).where(Folder.id == owner.home_folder_id)
    return session.execute(stmt).scalars().one()


def get_or_create_folder(
    session: Session,
    title: str,
    parent: Folder,
    ownership: Ownership,
) -> Folder:
    """Get existing folder or create new one with ownership."""
    stmt = select(Folder).where(
        Folder.parent_id == parent.id,
        Folder.title == title,
    )
    folder = session.execute(stmt).scalars().one_or_none()

    if folder is not None:
        return folder

    folder_id = uuid.uuid4()
    folder = Folder(
        id=folder_id,
        title=title,
        parent_id=parent.id,
        lang="en",
        ctype="folder",
    )
    session.add(folder)

    folder_ownership = Ownership(
        owner_type=ownership.owner_type,
        owner_id=ownership.owner_id,
        resource_type="node",
        resource_id=folder_id,
    )
    session.add(folder_ownership)
    session.commit()

    return folder


def mkdir(session: Session, path: str, ownership: Ownership) -> Folder:
    """Create folder hierarchy from path.

    Creates all folders in the path under the owner's home folder.
    If path ends with '/', all segments are treated as folders.
    Otherwise, the last segment is treated as a filename and excluded.

    Example:
        mkdir('/Invoices/2025/', ownership) creates:
        /home/Invoices/2025/

        mkdir('/Invoices/2025/invoice.pdf', ownership) creates:
        /home/Invoices/2025/
    """
    parent = get_owner_home_folder(session, ownership)

    stripped_path = path.strip()
    if stripped_path.endswith("/"):
        path_parts = [PurePath(stripped_path), *PurePath(stripped_path).parents]
    else:
        path_parts = PurePath(stripped_path).parents

    skip_names = {".", "/", "home", ".home"}

    for part in reversed(path_parts):
        if part == PurePath(".") or part == PurePath("/"):
            continue
        if part.name in skip_names:
            continue

        parent = get_or_create_folder(
            session,
            title=part.name,
            parent=parent,
            ownership=ownership,
        )

    return parent


def create_target_folder(
    session: Session, document_id: uuid.UUID
) -> Tuple[str, Folder]:
    """Create target folder structure for a document.

    Evaluates the document's path template and creates the necessary
    folder hierarchy with the same ownership as the document.

    Returns:
        Tuple of (evaluated_path, target_folder)
    """
    context = get_document_context(session, document_id)
    path_template = get_path_template(session, document_id)
    evaluated_path = get_evaluated_path(context, path_template)

    ownership = get_node_ownership(session, document_id)
    target_folder = mkdir(session, path=evaluated_path, ownership=ownership)

    return evaluated_path, target_folder


def move_document(session: Session, document_id: uuid.UUID) -> None:
    """Move document to its evaluated path template location.

    Evaluates the document's path template based on its document type,
    creates the target folder structure, and moves the document.
    The document title may be updated if the path template specifies a filename.
    """
    stmt = select(Document).where(Document.id == document_id)
    document = session.execute(stmt).scalars().one()

    evaluated_path, target_folder = create_target_folder(session, document_id)

    stripped_path = evaluated_path.strip()
    if not stripped_path.endswith("/"):
        document.title = PurePath(stripped_path).name

    document.parent_id = target_folder.id
    session.commit()
