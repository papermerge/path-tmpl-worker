import uuid

from pydantic import BaseModel

class DocumentContext(BaseModel):
    id: uuid.UUID
    title: str
