import uuid
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from path_tmpl_worker.db.base import Base

CType = Literal["document", "folder"]


class DocumentTypeCustomField(Base):
    __tablename__ = "document_type_custom_field"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_type_id: Mapped[UUID] = mapped_column(ForeignKey("document_types.id"))

    custom_field_id: Mapped[UUID] = mapped_column(ForeignKey("custom_fields.id"))


class Node(Base):
    __tablename__ = "core_basetreenode"

    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType] = mapped_column(insert_default="document")
    user: Mapped["User"] = relationship(primaryjoin="User.id == Node.user_id")
    user_id: Mapped[UUID] = mapped_column(ForeignKey("core_user.id", use_alter=True))
    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_basetreenode.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(), onupdate=func.now()
    )


class Folder(Node):
    __tablename__ = "core_folder"

    id: Mapped[UUID] = mapped_column(
        "basetreenode_ptr_id",
        ForeignKey("core_basetreenode.id"),
        primary_key=True,
        insert_default=uuid.uuid4(),
    )

    __mapper_args__ = {
        "polymorphic_identity": "folder",
    }


class Document(Node):
    __tablename__ = "core_document"

    id: Mapped[UUID] = mapped_column(
        "basetreenode_ptr_id",
        ForeignKey("core_basetreenode.id"),
        primary_key=True,
        insert_default=uuid.uuid4(),
    )
    document_type: Mapped["DocumentType"] = relationship(  # noqa: F821
        primaryjoin="DocumentType.id == Document.document_type_id",
    )
    document_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_types.id"), nullable=True
    )


class DocumentType(Base):
    __tablename__ = "document_types"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    path_template: Mapped[str] = mapped_column(nullable=True)
    custom_fields: Mapped[list["CustomField"]] = relationship(  #  noqa: F821
        secondary="document_type_custom_field"
    )
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())


class CustomField(Base):
    __tablename__ = "custom_fields"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    type: Mapped[str]
    extra_data: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_document.basetreenode_ptr_id")
    )
    field_id: Mapped[UUID] = mapped_column(ForeignKey("custom_fields.id"))
    value_text: Mapped[str] = mapped_column(nullable=True)
    value_boolean: Mapped[bool] = mapped_column(nullable=True)
    value_date: Mapped[datetime] = mapped_column(nullable=True)
    value_int: Mapped[int] = mapped_column(nullable=True)
    value_float: Mapped[float] = mapped_column(nullable=True)
    value_monetary: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())

    def __repr__(self):
        return f"CustomFieldValue(ID={self.id})"


class User(Base):
    __tablename__ = "core_user"

    id: Mapped[UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    username: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    first_name: Mapped[str] = mapped_column(default=" ")
    last_name: Mapped[str] = mapped_column(default=" ")
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_staff: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    home_folder_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_folder.basetreenode_ptr_id", deferrable=True)
    )
    home_folder: Mapped["Folder"] = relationship(
        primaryjoin="User.home_folder_id == Folder.id",
        viewonly=True,
    )
    inbox_folder_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "core_folder.basetreenode_ptr_id",
            deferrable=True,
        )
    )
    inbox_folder: Mapped["Folder"] = relationship(
        primaryjoin="User.home_folder_id == Folder.id",
        viewonly=True,
    )
    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())
    date_joined: Mapped[datetime] = mapped_column(insert_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(), onupdate=func.now()
    )
