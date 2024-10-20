import uuid

import typer

from path_tmpl_worker import api
from path_tmpl_worker.db import get_db

app = typer.Typer(help="CLI for Path Template worker")


@app.command()
def move_document(document_id: uuid.UUID):
    db_session = get_db()
    api.move_document(db_session, document_id)
