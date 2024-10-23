import uuid
from enum import Enum
from datetime import date
from pathlib import PurePath
from typing import TypeAlias, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class CustomFieldType(str, Enum):
    text = "text"
    date = "date"
    boolean = "boolean"
    int = "int"
    float = "float"
    monetary = "monetary"


class CustomField(BaseModel):
    id: uuid.UUID
    name: str
    type: CustomFieldType
    extra_data: str | None

    # Config
    model_config = ConfigDict(from_attributes=True)


CFValueType: TypeAlias = str | int | date | bool | float | None


class DocumentType(BaseModel):
    id: uuid.UUID
    name: str
    path_template: str | None = None
    custom_fields: list[CustomField]

    # Config
    model_config = ConfigDict(from_attributes=True)


class CFV(BaseModel):
    # custom field value
    # `core_documents.id`
    document_id: uuid.UUID
    # `core_documents.document_type_id`
    document_type_id: uuid.UUID
    # `custom_fields.id`
    custom_field_id: uuid.UUID
    # `custom_fields.name`
    name: str
    # `custom_fields.type`
    type: CustomFieldType
    # `custom_fields.extra_data`
    custom_field_value_id: uuid.UUID | None = None
    # `custom_field_values.value_text` or `custom_field_values.value_int` or ...
    value: CFValueType = None


class DocumentCFV(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID
    title: str
    document_type_id: uuid.UUID | None = None
    custom_fields: list[tuple[str, CFValueType]]


class BulkUpdate(BaseModel):
    document_id: uuid.UUID
    ev_path: PurePath


class DocumentMovedNotification(BaseModel):
    # all documents will be moved to the same
    source_folder_id: uuid.UUID
    target_folder_id: uuid.UUID
    old_document_title: str
    new_document_title: str
    document_id: uuid.UUID
    user_id: uuid.UUID


class DocumentsMovedNotification(BaseModel):
    count: int
    document_type_name: str
    document_type_id: uuid.UUID
    user_id: uuid.UUID
    source_folder_ids: list[uuid.UUID]
    target_folder_ids: list[uuid.UUID]


class Event(BaseModel, Generic[T]):
    type: str
    payload: T
