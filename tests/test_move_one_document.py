from sqlalchemy import select

from path_tmpl_worker import db
from path_tmpl_worker.db import orm
from .utils import get_ancestors


def test_move_one_document(db_session, make_receipt):
    template_path = """
        /home/My Documents/Receipts/
    """
    doc = make_receipt(title="bon.pdf", path_template=template_path)
    db.move_document(db_session, document_id=doc.id)

    refreshed_doc = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc.id)
    ).scalar()

    # title did not change
    assert refreshed_doc.title == "bon.pdf"

    actual_breadcrumb = "/".join([a[1] for a in get_ancestors(db_session, doc.id)])
    actual_breadcrumb = "/" + actual_breadcrumb
    assert actual_breadcrumb == "/home/My Documents/Receipts/bon.pdf"
