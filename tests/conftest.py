import uuid
import pytest

from path_tmpl_worker.db import Base
from path_tmpl_worker.db.engine import engine, Session
from path_tmpl_worker.db import orm
from path_tmpl_worker import constants, types
from path_tmpl_worker.config import get_settings

config = get_settings()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine, checkfirst=False)
    with Session() as session:
        yield session

    Base.metadata.drop_all(engine, checkfirst=False)


@pytest.fixture
def make_document_type(db_session: Session):

    def _maker(
        name: str,
        ownership: orm.Ownership,
        path_template: str | None = None,
    ):
        dtype_id = uuid.uuid4()
        dtype = orm.DocumentType(
            id=dtype_id,
            name=name,
            path_template=path_template,
        )
        db_session.add(dtype)

        dtype_ownership = orm.Ownership(
            owner_type=ownership.owner_type,
            owner_id=ownership.owner_id,
            resource_type="document_type",
            resource_id=dtype_id,
        )
        db_session.add(dtype_ownership)
        db_session.commit()

        return dtype

    return _maker


@pytest.fixture()
def make_document(db_session: Session):

    def _maker(
        title: str,
        parent: orm.Folder,
        ownership: orm.Ownership,
        document_type: orm.DocumentType | None = None,
        lang: str = "de",
    ):
        doc_id = uuid.uuid4()
        doc = orm.Document(
            id=doc_id,
            ctype="document",
            title=title,
            lang=lang,
            parent_id=parent.id,
            document_type=document_type,
        )
        db_session.add(doc)

        doc_ownership = orm.Ownership(
            owner_type=ownership.owner_type,
            owner_id=ownership.owner_id,
            resource_type="node",
            resource_id=doc_id,
        )
        db_session.add(doc_ownership)
        db_session.commit()

        return doc

    return _maker


@pytest.fixture()
def make_document_version(db_session: Session):

    def _maker(
        document: orm.Document,
        file_name: str,
        number: int = 1,
        size: int = 0,
    ):
        version = orm.DocumentVersion(
            id=uuid.uuid4(),
            document_id=document.id,
            file_name=file_name,
            number=number,
            size=size,
        )
        db_session.add(version)
        db_session.commit()

        return version

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
        db_session.add(db_user)

        db_home = orm.Folder(
            id=home_id,
            title=constants.HOME_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
        )
        db_session.add(db_home)

        db_inbox = orm.Folder(
            id=inbox_id,
            title=constants.INBOX_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            parent_id=home_id,
        )
        db_session.add(db_inbox)

        # Create ownership for home and inbox folders
        home_ownership = orm.Ownership(
            owner_type="user",
            owner_id=user_id,
            resource_type="node",
            resource_id=home_id,
        )
        db_session.add(home_ownership)

        inbox_ownership = orm.Ownership(
            owner_type="user",
            owner_id=user_id,
            resource_type="node",
            resource_id=inbox_id,
        )
        db_session.add(inbox_ownership)

        # Create special folder records
        home_special = orm.SpecialFolder(
            owner_type="user",
            owner_id=user_id,
            folder_type=types.FolderType.HOME,
            folder_id=home_id,
        )
        db_session.add(home_special)

        inbox_special = orm.SpecialFolder(
            owner_type="user",
            owner_id=user_id,
            folder_type=types.FolderType.INBOX,
            folder_id=inbox_id,
        )
        db_session.add(inbox_special)

        db_session.commit()

        return db_user

    return _maker


@pytest.fixture()
def make_group(db_session: Session):

    def _maker(name: str):
        group_id = uuid.uuid4()
        home_id = uuid.uuid4()
        inbox_id = uuid.uuid4()

        db_group = orm.Group(
            id=group_id,
            name=name,
        )
        db_session.add(db_group)

        db_home = orm.Folder(
            id=home_id,
            title=constants.HOME_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
        )
        db_session.add(db_home)

        db_inbox = orm.Folder(
            id=inbox_id,
            title=constants.INBOX_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            parent_id=home_id,
        )
        db_session.add(db_inbox)

        # Create ownership for home and inbox folders
        home_ownership = orm.Ownership(
            owner_type="group",
            owner_id=group_id,
            resource_type="node",
            resource_id=home_id,
        )
        db_session.add(home_ownership)

        inbox_ownership = orm.Ownership(
            owner_type="group",
            owner_id=group_id,
            resource_type="node",
            resource_id=inbox_id,
        )
        db_session.add(inbox_ownership)

        # Create special folder records
        home_special = orm.SpecialFolder(
            owner_type="group",
            owner_id=group_id,
            folder_type=types.FolderType.HOME,
            folder_id=home_id,
        )
        db_session.add(home_special)

        inbox_special = orm.SpecialFolder(
            owner_type="group",
            owner_id=group_id,
            folder_type=types.FolderType.INBOX,
            folder_id=inbox_id,
        )
        db_session.add(inbox_special)

        db_session.commit()

        return db_group

    return _maker


@pytest.fixture()
def user(make_user) -> orm.User:
    return make_user(username="random")


@pytest.fixture()
def user_ownership(user: orm.User) -> orm.Ownership:
    """Helper to create an Ownership-like object for a user."""
    return orm.Ownership(
        owner_type="user",
        owner_id=user.id,
        resource_type="node",  # placeholder, will be set per resource
        resource_id=user.id,  # placeholder
    )
