import uuid
from datetime import datetime, date
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Template

from path_tmpl_worker import models
from path_tmpl_worker.models import CustomField


def datefmt(value: datetime | date, format: str) -> str:
    return value.strftime(format=format)


template_env = SandboxedEnvironment()
template_env.filters["datefmt"] = datefmt


def get_evaluated_path(
    title: str,
    id: uuid.UUID,
    path_template: str,
    custom_fields: list[CustomField] | None = None,
) -> str:
    if custom_fields is None:
        custom_fields = []
    doc_ctx = models.DocumentContext(id=id, title=title, custom_fields=custom_fields)
    context = {"document": doc_ctx}
    template = template_env.from_string(
        path_template,
        template_class=Template,
    )
    rendered_template = template.render(context)

    return rendered_template.strip()
