import uuid
import pytest

from sqlalchemy.orm import Session

from path_tmpl_worker.db import Base, get_engine
from path_tmpl_worker.db import orm
from path_tmpl_worker import models


engine = get_engine("sqlite:///test_db.sqlite3")


@pytest.fixture(autouse=True, scope="session")
def db_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)



@pytest.fixture()
def db_session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def make_custom_field(db_session: Session):
    def _make_custom_field(name: str, type: models.CustomFieldType):
        cfield = orm.CustomField(
            id=uuid.uuid4(),
            name=name,
            type=type,
        )
        db_session.add(cfield)
        db_session.commit()

        return cfield

    return _make_custom_field

@pytest.fixture
def make_document_type_groceries(db_session: Session, make_custom_field):

    def _maker(title: str, path_template: str | None = None):
        cf1 = make_custom_field(name="Shop", type=models.CustomFieldType.text)
        cf2 = make_custom_field(name="Total", type=models.CustomFieldType.monetary)
        cf3 = make_custom_field(name="EffectiveDate", type=models.CustomFieldType.date)

        dtype = orm.DocumentType(
            id=uuid.uuid4(),
            name=title,
            custom_fields=[cf1, cf2, cf3],
            path_template=path_template
        )
        db_session.add(dtype)
        db_session.commit()

        return dtype

    return _maker


@pytest.fixture()
def make_receipt(db_session, make_document_type_groceries):

    def _maker(title: str, path_template: str | None = None):
        dtype = make_document_type_groceries(title="Groceries", path_template=path_template)
        doc_id = uuid.uuid4()
        doc = orm.Document(
            id=doc_id,
            ctype="document",
            document_type=dtype,
            title=title,
        )

        db_session.add(doc)

        db_session.commit()

        return doc

    return _maker
