import sys

import typer
from celery import Celery
from path_tmpl_worker import config, utils
from celery.signals import setup_logging


settings = config.get_settings()

if not settings.papermerge__redis__url:
    typer.secho(
        "Error: PAPERMERGE__REDIS__URL is not set.",
        fg=typer.colors.RED,
        bold=True,
        err=True,
    )
    sys.exit(1)

app = Celery(
    "PathTmplWorker",
    broker=settings.papermerge__redis__url,
    include=["path_tmpl_worker.tasks"],
)

app.conf.update(
    result_expires=3600,
    task_default_retry_delay=3,
    task_max_retries=3,
    broker_connection_retry_on_startup=False,
)

@setup_logging.connect
def config_loggers(*args, **kwargs):
    if settings.papermerge__main__logging_cfg:
        utils.setup_logging(settings.papermerge__main__logging_cfg)


if __name__ == "__main__":
    app.start()
