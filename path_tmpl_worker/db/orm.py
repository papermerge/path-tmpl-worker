import uuid
from typing import Literal

from sqlalchemy import ForeignKey, String, func, UniqueConstraint, Index, text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, CheckConstraint, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID


from path_tmpl_worker.utils import utc_now
from path_tmpl_worker import constants as const
from path_tmpl_worker import types
from path_tmpl_worker.db.base import Base

CType = Literal["document", "folder"]


class AuditColumns:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utc_now, onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Audit user foreign keys
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    archived_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class User(Base, AuditColumns):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4)
    username: Mapped[str] = mapped_column(
        String(const.USERNAME_MAX_LENGTH), unique=True
    )
    email: Mapped[str] = mapped_column(String(const.EMAIL_MAX_LENGTH), unique=True)
    password: Mapped[str] = mapped_column(
        String(const.PASSWORD_MAX_LENGTH), nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(
        String(const.NAME_MAX_LENGTH), default=None
    )
    last_name: Mapped[str | None] = mapped_column(
        String(const.NAME_MAX_LENGTH), default=None
    )
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_staff: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=False)

    special_folders: Mapped[list["SpecialFolder"]] = relationship(
        "SpecialFolder",
        primaryjoin=(
            "and_("
            "foreign(SpecialFolder.owner_id) == User.id, "
            "SpecialFolder.owner_type == 'user'"
            ")"
        ),
        viewonly=True,
        lazy="selectin",  # Eager load special folders with user
        cascade="delete",  # Delete special folders when user is deleted
    )

    date_joined: Mapped[datetime] = mapped_column(insert_default=func.now())

    @property
    def home_folder_id(self) -> UUID | None:
        """
        Get the home folder ID for this user.

        This property provides backward compatibility with code that expects
        home_folder_id to be a column on the User model.

        Returns:
            UUID of home folder, or None if not found
        """
        # Import here to avoid circular imports

        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.HOME:
                return sf.folder_id
        return None

    @property
    def inbox_folder_id(self) -> UUID | None:
        """
        Get the inbox folder ID for this user.

        This property provides backward compatibility with code that expects
        inbox_folder_id to be a column on the User model.

        Returns:
            UUID of inbox folder, or None if not found
        """
        # Import here to avoid circular imports
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.INBOX:
                return sf.folder_id
        return None

    @property
    def home_folder(self) -> "Folder | None":
        """
        Get the home Folder object for this user.

        Returns:
            Folder object or None if not found
        """
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.HOME:
                return sf.folder
        return None

    @property
    def inbox_folder(self) -> "Folder | None":
        """
        Get the inbox Folder object for this user.

        Returns:
            Folder object or None if not found
        """
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.INBOX:
                return sf.folder
        return None

    def __repr__(self):
        return f"User({self.id=}, {self.username=})"

    __mapper_args__ = {"confirm_deleted_rows": False}


class DocumentType(Base):
    __tablename__ = "document_types"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    path_template: Mapped[str] = mapped_column(nullable=True)


class Node(Base, AuditColumns):
    __tablename__ = "nodes"

    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType]
    lang: Mapped[str] = mapped_column(String(8), default="deu")

    parent_id: Mapped[UUID] = mapped_column(ForeignKey("nodes.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "node",
        "polymorphic_on": "ctype",
        "confirm_deleted_rows": False,
    }

    __table_args__ = (
        # Partial unique index: only folders with same title under same parent are prevented
        # This uses a partial index with a WHERE clause to only apply to folders
        Index(
            "idx_nodes_unique_folder_title_parent",
            "title",
            "parent_id",
            unique=True,
            postgresql_where=text("ctype = 'folder'"),
        ),
    )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.title!r})"


class Folder(Node):
    __tablename__ = "folders"

    id: Mapped[UUID] = mapped_column(
        "node_id",
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
        insert_default=uuid.uuid4,
    )

    __mapper_args__ = {
        "polymorphic_identity": "folder",
    }


class Document(Node):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        "node_id",
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_type: Mapped[DocumentType] = relationship(  # noqa: F821
        primaryjoin="DocumentType.id == Document.document_type_id"
    )
    document_type_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "document_types.id",
            name="documents_document_type_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "document",
    }


class DocumentVersion(Base, AuditColumns):
    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(default=1)
    file_name: Mapped[str] = mapped_column(nullable=True)
    size: Mapped[int] = mapped_column(default=0)
    checksum: Mapped[str] = mapped_column(nullable=True)
    checksum_algorithm: Mapped[str] = mapped_column(nullable=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.node_id", ondelete="CASCADE")
    )
    document: Mapped[Document] = relationship(back_populates="versions")
    lang: Mapped[str] = mapped_column(default="deu")
    text: Mapped[str] = mapped_column(nullable=True)

    page_count: Mapped[int] = mapped_column(default=0)
    short_description: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"DocumentVersion(id={self.id}, number={self.number})"


class UserGroup(Base):
    """Association table between users and groups"""

    __tablename__ = "users_groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    # Relationships
    group: Mapped["Group"] = relationship(
        "Group", back_populates="user_groups", foreign_keys=[group_id]
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="user_groups", foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"UserGroup({self.id=}, {self.group=}, {self.user=})"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)

    special_folders: Mapped[list["SpecialFolder"]] = relationship(
        "SpecialFolder",
        primaryjoin=(
            "and_("
            "foreign(SpecialFolder.owner_id) == Group.id, "
            "SpecialFolder.owner_type == 'group'"
            ")"
        ),
        viewonly=True,
        lazy="selectin",  # Eager load special folders with group
        cascade="delete",  # Delete special folders when group is deleted
    )

    user_groups: Mapped[list["UserGroup"]] = relationship(
        "UserGroup", back_populates="group"
    )

    @property
    def home_folder_id(self) -> UUID | None:
        """
        Get the home folder ID for this group.

        This property provides backward compatibility with code that expects
        home_folder_id to be a column on the Group model.

        Returns:
            UUID of home folder, or None if not found
        """
        # Import here to avoid circular imports
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.HOME:
                return sf.folder_id
        return None

    @property
    def inbox_folder_id(self) -> UUID | None:
        """
        Get the inbox folder ID for this group.

        This property provides backward compatibility with code that expects
        inbox_folder_id to be a column on the Group model.

        Returns:
            UUID of inbox folder, or None if not found
        """
        # Import here to avoid circular imports
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.INBOX:
                return sf.folder_id
        return None

    @property
    def home_folder(self) -> "Folder | None":
        """
        Get the home Folder object for this group.

        Returns:
            Folder object or None if not found
        """
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.HOME:
                return sf.folder
        return None

    @property
    def inbox_folder(self) -> "Folder | None":
        """
        Get the inbox Folder object for this group.

        Returns:
            Folder object or None if not found
        """
        for sf in self.special_folders:
            if sf.folder_type == types.FolderType.INBOX:
                return sf.folder
        return None

    @property
    def has_special_folders(self) -> bool:
        """
        Check if this group has both home and inbox folders.

        Returns:
            True if group has both home and inbox, False otherwise
        """
        folder_types = {sf.folder_type for sf in self.special_folders}
        return (
            types.FolderType.HOME in folder_types
            and types.FolderType.INBOX in folder_types
        )

    # Convenience property
    @property
    def active_users(self):
        """Get list of active (non-deleted) users in this group"""
        return [ug.user for ug in self.user_groups if ug.deleted_at is None]

    def __str__(self):
        return f"Group(name={self.name}, id={self.id})"

    def __repr__(self):
        return str(self)


class Ownership(Base):
    """
    Central table managing ownership relationships.

    One resource can have ONE owner (enforced by unique constraint).
    If you need multi-ownership in future, remove the unique constraint.
    """

    __tablename__ = "ownerships"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Who owns it
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # What is owned
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # Ensure valid owner types
        CheckConstraint(
            "owner_type IN ('user', 'group')", name="ownerships_owner_type_check"
        ),
        # Ensure valid resource types
        CheckConstraint(
            "resource_type IN ('node', 'custom_field', 'document_type', 'tag')",
            name="ownerships_resource_type_check",
        ),
        # ONE owner per resource (remove if you want multi-ownership)
        UniqueConstraint("resource_type", "resource_id", name="uq_resource_owner"),
        # Fast lookups by owner
        Index("idx_ownerships_owner", "owner_type", "owner_id"),
        # Fast lookups by resource
        Index("idx_ownerships_resource", "resource_type", "resource_id"),
        # Composite index for filtered queries
        Index(
            "idx_ownerships_owner_resource", "owner_type", "owner_id", "resource_type"
        ),
    )

    def __repr__(self):
        return (
            f"<Ownership(id={self.id}, "
            f"{self.resource_type}:{self.resource_id} -> "
            f"{self.owner_type}:{self.owner_id})>"
        )
