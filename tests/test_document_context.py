import uuid
from datetime import date as Date

from path_tmpl_worker.models import DocumentContext, CustomField


def test_document_context_basic():
    doc = DocumentContext(title="momo", id=uuid.uuid4(), custom_fields=[
        CustomField(name="Shop", value="lidl"),
        CustomField(name="Total", value=10.34),
        CustomField(name="Effective Date", value=Date(2024, 12, 23))
    ])

    assert doc.cf["Total"] == 10.34
    assert doc.cf["Shop"] == "lidl"
    assert doc.cf["Effective Date"] == Date(2024, 12, 23)
    assert doc.has_all_cf == True


def test_document_context_without_cf():
    doc = DocumentContext(title="momo", id=uuid.uuid4())

    assert doc.cf["Total"] is None
    assert doc.cf["Shop"] is None
    assert doc.has_all_cf == False

def test_document_context_has_some_cf_missing():
    doc = DocumentContext(title="momo", id=uuid.uuid4(),custom_fields=[
        CustomField(name="Shop", value="lidl"),
        CustomField(name="Total", value=None),
        CustomField(name="Effective Date", value=Date(2024, 12, 23))
    ])

    assert doc.has_all_cf == False
    assert doc.cf["Total"] is None
