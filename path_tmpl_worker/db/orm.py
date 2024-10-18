import uuid
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from path_tmpl_worker.db.base import Base

CType = Literal["document", "folder"]


class Node(Base):
    __tablename__ = "core_basetreenode"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, insert_default=uuid.uuid4()
    )
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType] = mapped_column(insert_default="document")
    user_id: Mapped[UUID]
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


class Document(Base):
    __tablename__ = "core_document"

    id: Mapped[UUID] = mapped_column(
        "basetreenode_ptr_id",
        ForeignKey("core_basetreenode.id"),
        primary_key=True,
        insert_default=uuid.uuid4(),
    )
    ctype: Mapped[CType]
    title: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[UUID]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(), onupdate=func.now()
    )
