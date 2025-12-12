import uuid

import pytest
from sqlalchemy import select

from path_tmpl_worker import db
from path_tmpl_worker.db import orm
from path_tmpl_worker.types import OwnerType, FolderType


def test_get_path_template(
    db_session, make_user, make_document_type, make_document_version
):
    user = make_user("alice")
    dtype = make_document_type(
        name="Invoice",
        owner_type="user",
        owner_id=user.id,
        path_template="/Invoices/{{ year }}/{{ file_name }}",
    )

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        document_type=dtype,
        title="invoice.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)
    db_session.commit()

    result = db.get_path_template(db_session, doc_id)

    assert result == "/Invoices/{{ year }}/{{ file_name }}"


def test_get_path_template_returns_none_when_no_document_type(db_session, make_user):
    user = make_user("alice")

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        title="invoice.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)
    db_session.commit()

    result = db.get_path_template(db_session, doc_id)

    assert result is None


def test_get_document_context(
    db_session, make_user, make_document_type, make_document_version
):
    user = make_user("alice")
    dtype = make_document_type(
        name="Receipt",
        owner_type="user",
        owner_id=user.id,
    )

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        document_type=dtype,
        title="receipt.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)
    db_session.commit()

    make_document_version(document=doc, file_name="receipt_v1.pdf", number=1)

    context = db.get_document_context(db_session, doc_id)

    assert context.id == doc_id
    assert context.title == "receipt.pdf"
    assert context.file_name == "receipt_v1.pdf"
    assert context.category == "Receipt"
    assert context.year is not None
    assert context.month is not None
    assert context.day is not None


def test_get_document_context_uses_latest_version(
    db_session, make_user, make_document_type, make_document_version
):
    user = make_user("alice")
    dtype = make_document_type(
        name="Receipt",
        owner_type="user",
        owner_id=user.id,
    )

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        document_type=dtype,
        title="receipt.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)
    db_session.commit()

    make_document_version(document=doc, file_name="receipt_v1.pdf", number=1)
    make_document_version(document=doc, file_name="receipt_v2.pdf", number=2)
    make_document_version(document=doc, file_name="receipt_v3.pdf", number=3)

    context = db.get_document_context(db_session, doc_id)

    assert context.file_name == "receipt_v3.pdf"


def test_get_document_context_empty_category_when_no_document_type(
    db_session, make_user, make_document_version
):
    user = make_user("alice")

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        title="receipt.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)
    db_session.commit()

    make_document_version(document=doc, file_name="receipt.pdf", number=1)

    context = db.get_document_context(db_session, doc_id)

    assert context.category == ""


def test_get_node_ownership(db_session, make_user):
    user = make_user("alice")

    doc_id = uuid.uuid4()
    doc = orm.Document(
        id=doc_id,
        ctype="document",
        title="test.pdf",
        lang="de",
        parent_id=user.home_folder_id,
    )
    db_session.add(doc)

    doc_ownership = orm.Ownership(
        owner_type="user",
        owner_id=user.id,
        resource_type="node",
        resource_id=doc_id,
    )
    db_session.add(doc_ownership)
    db_session.commit()

    ownership = db.get_node_ownership(db_session, doc_id)

    assert ownership.owner_type == "user"
    assert ownership.owner_id == user.id
    assert ownership.resource_type == "node"
    assert ownership.resource_id == doc_id


def test_get_owner_home_folder_for_user(db_session, make_user):
    user = make_user("alice")

    # Get ownership of user's home folder
    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    home_folder = db.get_owner_home_folder(db_session, ownership)

    assert home_folder.id == user.home_folder_id
    assert home_folder.title == "home"


def test_get_or_create_folder_creates_new_folder(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    home_folder = db.get_owner_home_folder(db_session, ownership)

    new_folder = db.get_or_create_folder(
        db_session,
        title="My Documents",
        parent=home_folder,
        ownership=ownership,
    )

    assert new_folder.title == "My Documents"
    assert new_folder.parent_id == home_folder.id

    # Verify ownership was created
    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == new_folder.id)
    folder_ownership = db_session.execute(stmt).scalars().one()
    assert folder_ownership.owner_type == "user"
    assert folder_ownership.owner_id == user.id


def test_get_or_create_folder_returns_existing_folder(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    home_folder = db.get_owner_home_folder(db_session, ownership)

    # Create folder first time
    folder1 = db.get_or_create_folder(
        db_session,
        title="My Documents",
        parent=home_folder,
        ownership=ownership,
    )

    # Try to create same folder again
    folder2 = db.get_or_create_folder(
        db_session,
        title="My Documents",
        parent=home_folder,
        ownership=ownership,
    )

    assert folder1.id == folder2.id


def test_mkdir_creates_folder_hierarchy(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    target_folder = db.mkdir(
        db_session,
        path="/My Documents/Invoices/2025/",
        ownership=ownership,
    )

    assert target_folder.title == "2025"

    # Verify hierarchy
    ancestors = db.get_ancestors(db_session, target_folder.id)
    titles = [a[1] for a in ancestors]

    assert titles == ["home", "My Documents", "Invoices", "2025"]


def test_mkdir_excludes_filename_when_path_does_not_end_with_slash(
    db_session, make_user
):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    target_folder = db.mkdir(
        db_session,
        path="/Invoices/2025/invoice.pdf",
        ownership=ownership,
    )

    assert target_folder.title == "2025"

    ancestors = db.get_ancestors(db_session, target_folder.id)
    titles = [a[1] for a in ancestors]

    assert titles == ["home", "Invoices", "2025"]
    assert "invoice.pdf" not in titles


def test_mkdir_skips_home_in_path(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    target_folder = db.mkdir(
        db_session,
        path="/home/My Documents/",
        ownership=ownership,
    )

    assert target_folder.title == "My Documents"

    ancestors = db.get_ancestors(db_session, target_folder.id)
    titles = [a[1] for a in ancestors]

    # Should not have duplicate "home"
    assert titles == ["home", "My Documents"]


def test_mkdir_returns_home_folder_for_empty_path(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    target_folder = db.mkdir(
        db_session,
        path="/",
        ownership=ownership,
    )

    assert target_folder.id == user.home_folder_id


def test_create_target_folder(db_session, make_receipt):
    doc = make_receipt(
        title="grocery_receipt.pdf",
        path_template="/Receipts/{{ year }}/",
    )

    evaluated_path, target_folder = db.create_target_folder(db_session, doc.id)

    assert "/Receipts/" in evaluated_path
    assert target_folder.title == str(target_folder.title)  # year as string

    ancestors = db.get_ancestors(db_session, target_folder.id)
    titles = [a[1] for a in ancestors]

    assert titles[0] == "home"
    assert titles[1] == "Receipts"


def test_get_ancestors_includes_self(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    # Create a folder hierarchy
    db.mkdir(db_session, path="/A/B/C/", ownership=ownership)

    stmt = select(orm.Folder).where(orm.Folder.title == "C")
    folder_c = db_session.execute(stmt).scalars().one()

    ancestors = db.get_ancestors(db_session, folder_c.id, include_self=True)
    titles = [a[1] for a in ancestors]

    assert titles == ["home", "A", "B", "C"]


def test_get_ancestors_excludes_self(db_session, make_user):
    user = make_user("alice")

    stmt = select(orm.Ownership).where(orm.Ownership.resource_id == user.home_folder_id)
    ownership = db_session.execute(stmt).scalars().one()

    # Create a folder hierarchy
    db.mkdir(db_session, path="/A/B/C/", ownership=ownership)

    stmt = select(orm.Folder).where(orm.Folder.title == "C")
    folder_c = db_session.execute(stmt).scalars().one()

    ancestors = db.get_ancestors(db_session, folder_c.id, include_self=False)
    titles = [a[1] for a in ancestors]

    assert titles == ["home", "A", "B"]
