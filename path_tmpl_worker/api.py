import uuid
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Template

from path_tmpl_worker import models

template_environment = SandboxedEnvironment(
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=False,
    autoescape=False,
    extensions=["jinja2.ext.loopcontrols"],
)

def get_evaluated_path(title: str, id: uuid.UUID, path_template: str) -> str:
    doc_ctx = models.DocumentContext(id=id, title=title)
    context = ({
        "document": doc_ctx
    })
    template = template_environment.from_string(
        path_template,
        template_class=Template,
    )
    rendered_template = template.render(context)

    return rendered_template
