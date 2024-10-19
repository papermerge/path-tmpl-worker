import uuid
from enum import Enum
from datetime import date
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict


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


class CField(BaseModel):
    name: str
    value: CFValueType = None

    def __hash__(self):
        return hash(f"{self.name}-{self.value}")


class GetCFItem:
    def __init__(self, custom_fields: list[CField]):
        self.custom_fields = custom_fields

    def __getitem__(self, name: str):
        for cf in self.custom_fields:
            if cf.name == name:
                return cf.value

        return None


class DocumentContext(BaseModel):
    id: uuid.UUID
    title: str
    custom_fields: list[CField] = []

    @property
    def cf(self) -> GetCFItem:
        return GetCFItem(self.custom_fields)

    @property
    def has_all_cf(self) -> bool:
        if len(self.custom_fields) == 0:
            return False

        for cf in self.custom_fields:
            if cf.value is None:
                return False

        return True


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
