import uuid
from enum import Enum
from datetime import date
from pathlib import PurePath
from typing import TypeAlias, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


T = TypeVar("T")


class CustomFieldType(str, Enum):
    text = "text"
    date = "date"
    boolean = "boolean"
    int = "int"
    float = "float"
    monetary = "monetary"
    # for salaries: e.g. "February, 2023"
    yearmonth = "yearmonth"


class CustomField(BaseModel):
    id: uuid.UUID
    name: str
    type: CustomFieldType
    extra_data: str | None

    # Config
    model_config = ConfigDict(from_attributes=True)


CFNameType: TypeAlias = str
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

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, value, info: ValidationInfo) -> CFValueType:
        if value and info.data["type"] == CustomFieldType.monetary:
            return float(value)

        return value


CustomFieldTupleType: TypeAlias = tuple[CFNameType, CFValueType, CustomFieldType]


class DocumentCFV(BaseModel):
    id: uuid.UUID  # document ID
    parent_id: uuid.UUID
    title: str
    document_type_id: uuid.UUID | None = None
    custom_fields: list[CustomFieldTupleType]

    @field_validator("custom_fields", mode="before")
    @classmethod
    def convert_value(cld, value, info: ValidationInfo) -> CFValueType:
        if value:
            new_value: list[CustomFieldTupleType] = []
            for item in value:
                if item[2] == CustomFieldType.monetary and item[1]:
                    new_item: CustomFieldTupleType = (item[0], float(item[1]), item[2])
                    new_value.append(new_item)
                else:
                    new_item: CustomFieldTupleType = (item[0], item[1], item[2])
                    new_value.append(new_item)

            return new_value

        return value


class BulkUpdate(BaseModel):
    document_id: uuid.UUID
    ev_path: str
    title: str


class DocumentMovedNotification(BaseModel):
    # all documents will be moved to the same
    source_folder_id: uuid.UUID
    target_folder_id: uuid.UUID
    old_document_title: str
    new_document_title: str
    document_id: uuid.UUID


class DocumentsMovedNotification(BaseModel):
    count: int
    document_type_name: str
    document_type_id: uuid.UUID
    source_folder_ids: list[uuid.UUID]
    target_folder_ids: list[uuid.UUID]


class Event(BaseModel, Generic[T]):
    type: str
    payload: T


class DocumentCFVWithIndex(BaseModel):
    dcfv: DocumentCFV
    index: int


class DocumentCFVRow(BaseModel):
    title: str
    doc_id: uuid.UUID
    document_type_id: uuid.UUID
    parent_id: uuid.UUID
    cf_name: CFNameType
    cf_type: CustomFieldType
    cf_value: CFValueType
