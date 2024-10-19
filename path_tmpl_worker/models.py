import uuid
from datetime import date
from typing import TypeAlias

from pydantic import BaseModel


CFValueType: TypeAlias = str | int | date | bool | float | None


class CustomField(BaseModel):
    name: str
    value: CFValueType = None


class GetCFItem:
    def __init__(self, custom_fields: list[CustomField]):
        self.custom_fields = custom_fields

    def __getitem__(self, name: str):
        for cf in self.custom_fields:
            if cf.name == name:
                return cf.value

        return None


class DocumentContext(BaseModel):
    id: uuid.UUID
    title: str
    custom_fields: list[CustomField] = []

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
