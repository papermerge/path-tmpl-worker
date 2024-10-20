import uuid
import pytest

from sqlalchemy.orm import Session

from path_tmpl_worker.db import Base, get_engine
from path_tmpl_worker.db import orm
from path_tmpl_worker import models, constants


engine = get_engine("sqlite:///test_db.sqlite3")


@pytest.fixture(autouse=True, scope="function")
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
            path_template=path_template,
        )
        db_session.add(dtype)
        db_session.commit()

        return dtype

    return _maker


@pytest.fixture()
def make_receipt(db_session, make_user, make_document_type_groceries):

    def _maker(title: str, path_template: str | None = None):
        user = make_user("john")
        dtype = make_document_type_groceries(
            title="Groceries", path_template=path_template
        )
        doc_id = uuid.uuid4()
        doc = orm.Document(
            id=doc_id,
            ctype="document",
            document_type=dtype,
            title=title,
            user_id=user.id,
            lang="de",
        )

        db_session.add(doc)

        db_session.commit()

        return doc

    return _maker


@pytest.fixture()
def make_document(db_session, make_document_type_groceries):

    def _maker(title: str, user_id: uuid.UUID):
        doc_id = uuid.uuid4()
        doc = orm.Document(
            id=doc_id, ctype="document", title=title, user_id=user_id, lang="de"
        )

        db_session.add(doc)

        db_session.commit()

        return doc

    return _maker


@pytest.fixture()
def make_user(db_session: Session):
    def _maker(username: str):
        user_id = uuid.uuid4()
        home_id = uuid.uuid4()
        inbox_id = uuid.uuid4()

        db_user = orm.User(
            id=user_id,
            username=username,
            email=f"{username}@mail.com",
            first_name=f"{username}_first",
            last_name=f"{username}_last",
            is_superuser=True,
            is_active=True,
            password="pwd",
        )
        db_inbox = orm.Folder(
            id=inbox_id,
            title=constants.INBOX_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            user_id=user_id,
        )
        db_home = orm.Folder(
            id=home_id,
            title=constants.HOME_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            user_id=user_id,
        )
        db_session.add_all([db_home, db_inbox, db_user])
        db_user.home_folder_id = db_home.id
        db_user.inbox_folder_id = db_inbox.id
        db_session.commit()

        return db_user

    return _maker
