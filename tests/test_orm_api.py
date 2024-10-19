from sqlalchemy.orm import Session
from path_tmpl_worker.db import get_doc
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

    doc = get_doc(db_session, document_id=receipt.id)

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

    doc = get_doc(db_session, document_id=receipt.id)

    expected_cf = {
        CField(name="Shop", value=None),
        CField(name="Total", value=None),
        CField(name="EffectiveDate", value=None),
    }

    assert "invoice.pdf" == doc.title
    assert receipt.id == doc.id
    assert expected_cf == set(doc.custom_fields)
