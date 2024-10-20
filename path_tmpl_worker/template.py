from pathlib import PurePath
from datetime import datetime, date


from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Template


from path_tmpl_worker import models


def datefmt(value: datetime | date, format: str) -> str:
    return value.strftime(format=format)


template_env = SandboxedEnvironment()
template_env.filters["datefmt"] = datefmt


def get_evaluated_path(
    doc: models.DocumentContext,
    path_template: str,
) -> PurePath:
    context = {"document": doc}
    template = template_env.from_string(
        path_template,
        template_class=Template,
    )
    rendered_template = template.render(context)

    return PurePath(rendered_template.strip())
