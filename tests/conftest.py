import uuid
import pytest


from path_tmpl_worker.db import Base
from path_tmpl_worker.db.engine import engine, Session
from path_tmpl_worker.db import orm
from path_tmpl_worker import models, constants
from path_tmpl_worker.config import get_settings

config = get_settings()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine, checkfirst=False)
    with Session() as session:
        yield session

    Base.metadata.drop_all(engine, checkfirst=False)


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

    def _maker(title: str, user_id: uuid.UUID, path_template: str | None = None):
        cf1 = make_custom_field(name="Shop", type=models.CustomFieldType.text)
        cf2 = make_custom_field(name="Total", type=models.CustomFieldType.monetary)
        cf3 = make_custom_field(name="EffectiveDate", type=models.CustomFieldType.date)

        dtype = orm.DocumentType(
            id=uuid.uuid4(),
            name=title,
            user_id=user_id,
            custom_fields=[cf1, cf2, cf3],
            path_template=path_template,
        )
        db_session.add(dtype)
        db_session.commit()

        return dtype

    return _maker


@pytest.fixture()
def make_receipt(db_session, make_user, make_document_type_groceries):

    def _maker(
        title: str,
        path_template: str | None = None,
        dtype: orm.DocumentType | None = None,
        user: orm.User | None = None,
    ):
        if user is None:
            user = make_user("john")

        if dtype is None:
            dtype = make_document_type_groceries(
                title="Groceries", path_template=path_template, user_id=user.id
            )

        doc_id = uuid.uuid4()
        doc = orm.Document(
            id=doc_id,
            ctype="document",
            document_type=dtype,
            title=title,
            user_id=user.id,
            lang="de",
            parent_id=user.home_folder_id,
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
    def _maker(username: str, is_superuser: bool = True):
        user_id = uuid.uuid4()
        home_id = uuid.uuid4()
        inbox_id = uuid.uuid4()

        db_user = orm.User(
            id=user_id,
            username=username,
            email=f"{username}@mail.com",
            first_name=f"{username}_first",
            last_name=f"{username}_last",
            is_superuser=is_superuser,
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
        db_session.add(db_inbox)
        db_session.add(db_home)
        db_session.add(db_user)
        db_session.commit()
        db_user.home_folder_id = db_home.id
        db_user.inbox_folder_id = db_inbox.id
        db_session.commit()

        return db_user

    return _maker


@pytest.fixture()
def user(make_user) -> orm.User:
    return make_user(username="random")
