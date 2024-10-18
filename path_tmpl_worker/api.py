import uuid
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Template

template_environment = SandboxedEnvironment(
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=False,
    autoescape=False,
    extensions=["jinja2.ext.loopcontrols"],
)

def get_evaluated_path(document_id: uuid.UUID, path_template: str) -> str:
    context = (
        {"document": {}}
    )
    template = template_environment.from_string(
        path_template,
        template_class=Template,
    )
    rendered_template = template.render(context)

    return rendered_template
