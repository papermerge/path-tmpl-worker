from pathlib import PurePath

from sqlalchemy.orm import Session
from sqlalchemy import select
from path_tmpl_worker.db import get_doc_ctx, update_doc_cfv
from path_tmpl_worker.db.orm import Folder
from path_tmpl_worker.db.api import (
    get_user_home,
    mkdir_node,
    mkdir,
    get_user,
    get_path_template,
)
from path_tmpl_worker.models import CField


def test_basic_fixture(make_receipt):
    doc = make_receipt(
        title="invoice.pdf", path_template="/home/Receipts/{{document.id}}.pdf"
    )

    assert doc.title == "invoice.pdf"
    assert doc.document_type.path_template == "/home/Receipts/{{document.id}}.pdf"


def test_get_doc_empty_valued_custom_fields(db_session: Session, make_receipt):
    receipt = make_receipt(
        title="invoice.pdf", path_template="/home/Receipts/{{document.id}}.pdf"
    )

    doc = get_doc_ctx(db_session, document_id=receipt.id)

    expected_cf = {
        CField(name="Shop", value=None),
        CField(name="Total", value=None),
        CField(name="EffectiveDate", value=None),
    }

    assert "invoice.pdf" == doc.title
    assert receipt.id == doc.id
    assert expected_cf == set(doc.custom_fields)


def test_get_doc_non_emtpy_cf(db_session: Session, make_receipt):
    receipt = make_receipt(
        title="invoice.pdf", path_template="/home/Receipts/{{document.id}}.pdf"
    )

    # insert some non-empty values
    custom_fields = {"Total": 10.99, "Shop": "rewe"}
    update_doc_cfv(db_session, document_id=receipt.id, custom_fields=custom_fields)

    doc = get_doc_ctx(db_session, document_id=receipt.id)

    assert "invoice.pdf" == doc.title
    assert receipt.id == doc.id
    assert doc.cf["Shop"] == "rewe"
    assert doc.cf["EffectiveDate"] is None
    assert doc.cf["Total"] == 10.99


def test_get_user_home(db_session: Session, make_user):
    user = make_user("john")
    home = get_user_home(db_session, user.id)

    assert home.title == user.home_folder.title
    assert home.id == user.home_folder.id


def test_make_node_my_documents(db_session: Session, make_user):
    user = make_user("john")
    home = get_user_home(db_session, user.id)
    mydocs = mkdir_node(
        db_session, PurePath("My Documents"), parent=home, user_id=user.id
    )

    assert mydocs.parent_id == home.id
    assert mydocs.title == "My Documents"
    assert mydocs.user == user


def test_mkdir_basic(db_session: Session, make_user):
    user = make_user("john")
    path_to_make = PurePath("/home/My Documents/Invoices/file.pdf")
    last_node = mkdir(db_session, path_to_make, user_id=user.id)

    home = get_user_home(db_session, user_id=user.id)
    invoices = (
        db_session.execute(select(Folder).where(Folder.title == "Invoices"))
        .scalars()
        .one()
    )
    mydocs = (
        db_session.execute(select(Folder).where(Folder.title == "My Documents"))
        .scalars()
        .one()
    )

    assert invoices.parent_id == mydocs.id
    assert mydocs.parent_id == home.id
    assert last_node.id == invoices.id


def test_get_user(db_session: Session, make_user, make_document):
    user = make_user("john")
    doc = make_document(title="letter.pdf", user_id=user.id)

    document_user = get_user(db_session, doc.id)
    assert document_user == user


def test_get_template_path_with_existing_path_tmpl(db_session: Session, make_receipt):
    """
    Document with associated DocumentType which has non-empty path_template
    attribute
    """
    receipt = make_receipt(
        title="My receipt.pdf", path_template="/Groceries/{{document.title}}"
    )
    path_tmpl = get_path_template(db_session, document_id=receipt.id)

    assert path_tmpl == "/Groceries/{{document.title}}"


def test_get_template_path_with_empty_path_tmpl(db_session: Session, make_receipt):
    """
    Document with associated DocumentType which has empty path_template
    attribute
    """
    receipt = make_receipt(title="My receipt.pdf")
    path_tmpl = get_path_template(db_session, document_id=receipt.id)

    assert path_tmpl is None


def test_get_template_path_of_document_without_doctype(
    db_session: Session, make_document, make_user
):
    """Document has no associated DocumentType"""
    user = make_user("John")
    doc = make_document(title="My receipt.pdf", user_id=user.id)

    path_tmpl = get_path_template(db_session, document_id=doc.id)

    assert path_tmpl is None
