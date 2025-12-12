import uuid

from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict


T = TypeVar("T")



class DocumentType(BaseModel):
    id: uuid.UUID
    name: str
    path_template: str | None = None

    # Config
    model_config = ConfigDict(from_attributes=True)


class BulkUpdate(BaseModel):
    document_id: uuid.UUID
    ev_path: str
    title: str
