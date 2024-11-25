from sqlalchemy import select

from path_tmpl_worker import api
from path_tmpl_worker.db import orm
from path_tmpl_worker.db import api as dbapi
from .utils import get_ancestors


def test_move_document(db_session, make_receipt):
    template_path = """
        /home/My Documents/Receipts/
    """
    doc = make_receipt(title="bon.pdf", path_template=template_path)
    api.move_document(db_session, document_id=doc.id, user_id=doc.user_id)

    refreshed_doc = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc.id)
    ).scalar()

    # title did not change
    assert refreshed_doc.title == "bon.pdf"

    actual_breadcrumb = "/".join([a[1] for a in get_ancestors(db_session, doc.id)])
    actual_breadcrumb = "/" + actual_breadcrumb
    assert actual_breadcrumb == "/home/My Documents/Receipts/bon.pdf"


def test_move_documents(db_session, make_receipt):
    template_path = """
        /home/My Documents/Receipts/
    """
    doc = make_receipt(title="bon.pdf", path_template=template_path)
    api.move_documents(
        db_session, document_type_id=doc.document_type_id, user_id=doc.user_id
    )

    refreshed_doc = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc.id)
    ).scalar()

    actual_breadcrumb = "/".join([a[1] for a in get_ancestors(db_session, doc.id)])
    actual_breadcrumb = "/" + actual_breadcrumb
    assert actual_breadcrumb == "/home/My Documents/Receipts/bon.pdf"
    # title did not change
    assert refreshed_doc.title == "bon.pdf"


def test_move_documents_with_one_doc_with_cfv(db_session, make_receipt):
    template_path = """
    {% if document.cf['EffectiveDate'] %}
        /home/Receipts/{{ document.cf['Shop'] }}-{{document.cf['EffectiveDate']}}-{{document.id}}.pdf
    {% else %}
        /home/Receipts/{{ document.id }}.pdf
    {% endif %}
    """
    doc = make_receipt(title="my receipt.pdf", path_template=template_path)
    custom_fields = {"Total": 10.99, "Shop": "rewe", "EffectiveDate": "2024-11-18"}
    dbapi.update_doc_cfv(db_session, document_id=doc.id, custom_fields=custom_fields)

    api.move_documents(
        db_session, document_type_id=doc.document_type_id, user_id=doc.user_id
    )

    refreshed_doc = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc.id)
    ).scalar()

    actual_breadcrumb = "/".join([a[1] for a in get_ancestors(db_session, doc.id)])
    actual_breadcrumb = "/" + actual_breadcrumb

    assert refreshed_doc.title == f"rewe-2024-11-18-{doc.id}.pdf"
    assert actual_breadcrumb == f"/home/Receipts/rewe-2024-11-18-{doc.id}.pdf"


def test_move_documents_with_two_docs_with_cfv(
    db_session, make_receipt, make_document_type_groceries, user
):
    path_template = """
    {% if document.cf['EffectiveDate'] %}
        /home/Receipts/{{ document.cf['Shop'] }}-{{document.cf['EffectiveDate']}}-{{document.id}}.pdf
    {% else %}
        /home/Receipts/{{ document.id }}.pdf
    {% endif %}
    """
    dtype = make_document_type_groceries(
        title="Groceries", user_id=user.id, path_template=path_template
    )

    doc1 = make_receipt(title="my receipt.pdf", dtype=dtype, user=user)
    custom_fields1 = {"Total": 10.99, "Shop": "rewe", "EffectiveDate": "2024-11-18"}
    dbapi.update_doc_cfv(db_session, document_id=doc1.id, custom_fields=custom_fields1)
    doc2 = make_receipt(title="bon.pdf", dtype=dtype, user=user)
    custom_fields2 = {"Total": 5.25, "Shop": "lidl", "EffectiveDate": "2024-01-13"}
    dbapi.update_doc_cfv(db_session, document_id=doc2.id, custom_fields=custom_fields2)

    api.move_documents(db_session, document_type_id=dtype.id, user_id=doc1.user_id)

    refreshed_doc1 = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc1.id)
    ).scalar()

    refreshed_doc2 = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc2.id)
    ).scalar()

    actual_breadcrumb1 = "/".join([a[1] for a in get_ancestors(db_session, doc1.id)])
    actual_breadcrumb1 = "/" + actual_breadcrumb1
    actual_breadcrumb2 = "/".join([a[1] for a in get_ancestors(db_session, doc2.id)])
    actual_breadcrumb2 = "/" + actual_breadcrumb2

    assert refreshed_doc1.title == f"rewe-2024-11-18-{doc1.id}.pdf"
    assert actual_breadcrumb1 == f"/home/Receipts/rewe-2024-11-18-{doc1.id}.pdf"
    assert refreshed_doc2.title == f"lidl-2024-01-13-{doc2.id}.pdf"
    assert actual_breadcrumb2 == f"/home/Receipts/lidl-2024-01-13-{doc2.id}.pdf"
