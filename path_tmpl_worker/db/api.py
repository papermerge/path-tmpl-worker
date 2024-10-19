import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional, Iterable

from path_tmpl_worker import models
from path_tmpl_worker.constants import INCOMING_DATE_FORMAT


def get_doc(session: Session, document_id: uuid.UUID) -> models.DocumentContext:
    stmt = """
        SELECT
            doc.basetreenode_ptr_id,
            doc.title,
            cf.cf_name,
            cf.cf_type,
            CASE
                WHEN(cf.cf_type = 'monetary') THEN cfv.value_monetary
                WHEN(cf.cf_type = 'text') THEN cfv.value_text
                WHEN(cf.cf_type = 'date') THEN cfv.value_date
                WHEN(cf.cf_type = 'boolean') THEN cfv.value_boolean
            END AS cf_value
        FROM core_document AS doc
        JOIN document_type_custom_field AS dtcf ON dtcf.document_type_id = doc.document_type_id
        JOIN(
            SELECT
                sub_cf1.id AS cf_id,
                sub_cf1.name AS cf_name,
                sub_cf1.type AS cf_type,
                sub_cf1.extra_data AS cf_extra_data
            FROM core_document AS sub_doc1
            JOIN document_type_custom_field AS sub_dtcf1
                ON sub_dtcf1.document_type_id = sub_doc1.document_type_id
            JOIN custom_fields AS sub_cf1
                ON sub_cf1.id = sub_dtcf1.custom_field_id
            WHERE sub_doc1.basetreenode_ptr_id = :document_id
        ) AS cf ON cf.cf_id = dtcf.custom_field_id
        LEFT OUTER JOIN custom_field_values AS cfv
            ON cfv.field_id = cf.cf_id AND cfv.document_id = :document_id
    WHERE
        doc.basetreenode_ptr_id = :document_id
    """
    custom_fields = []
    str_doc_id = str(document_id).replace("-", "")
    doc_title = ""
    for row in session.execute(text(stmt), {"document_id": str_doc_id}):
        if row.cf_type == "date":
            value = str2date(row.cf_value)
        else:
            value = row.cf_value
        doc_title = row.title
        custom_fields.append(
            models.CField(
                name=row.cf_name,
                value=value,
            )
        )

    return models.DocumentContext(
        title=doc_title, id=document_id, custom_fields=custom_fields
    )


def str2date(value: str | None) -> Optional[datetime.date]:
    """Convert incoming user string to datetime.date"""
    # 10 = 4 Y chars +  1 "-" char + 2 M chars + 1 "-" char + 2 D chars
    if value is None:
        return None

    DATE_LEN = 10
    stripped_value = value.strip()
    if len(stripped_value) == 0:
        return None

    if len(stripped_value) < DATE_LEN and len(stripped_value) > 0:
        raise ValueError(
            f"{stripped_value} expected to have at least {DATE_LEN} characters"
        )

    return datetime.strptime(
        value[:DATE_LEN],
        INCOMING_DATE_FORMAT,
    ).date()
