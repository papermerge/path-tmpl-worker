from freezegun import freeze_time
from sqlalchemy import select

from path_tmpl_worker import db
from path_tmpl_worker.db import orm


def test_move_documents(db_session, make_receipt):
    template_path = """
        /My Documents/Receipts/
    """
    doc = make_receipt(title="bon.pdf", path_template=template_path)
    db.move_documents(db_session, document_type_id=doc.document_type_id)

    refreshed_doc = db_session.execute(
        select(orm.Document).where(orm.Document.id == doc.id)
    ).scalar()

    actual_breadcrumb = "/".join([a[1] for a in db.get_ancestors(db_session, doc.id)])
    actual_breadcrumb = "/" + actual_breadcrumb
    assert actual_breadcrumb == "/home/My Documents/Receipts/bon.pdf"
    # title did not change
    assert refreshed_doc.title == "bon.pdf"


@freeze_time("2024-12-26")
def test_move_documents_with_multiple_documents_in_category(
    db_session, make_receipt, make_document_type, make_user
):
    user = make_user("luke")
    path_template = "/My Documents/Receipts/{{ year }}/{{ title }}_{{ id }}"
    dtype = make_document_type(
        name="Groceries",
        path_template=path_template,
        owner_type="user",
        owner_id=user.id,
    )

    docs = []
    for _ in range(1, 5):
        doc = make_receipt(
            title="bon.pdf", path_template=path_template, dtype=dtype, user=user
        )
        docs.append(doc)

    db.move_documents(db_session, document_type_id=dtype.id)

    refreshed_doc = (
        db_session.execute(
            select(orm.Document).where(orm.Document.id.in_([doc.id for doc in docs]))
        )
        .scalars()
        .all()
    )

    for doc in refreshed_doc:
        actual_breadcrumb = "/".join(
            [a[1] for a in db.get_ancestors(db_session, doc.id)]
        )
        actual_breadcrumb = "/" + actual_breadcrumb
        assert actual_breadcrumb == f"/home/My Documents/Receipts/2024/bon.pdf_{doc.id}"
        assert doc.title == f"bon.pdf_{doc.id}"
