import uuid

import typer

from path_tmpl_worker import api
from path_tmpl_worker.db import get_db

app = typer.Typer(help="CLI for Path Template worker")


@app.command()
def move_document(document_id: uuid.UUID):
    with get_db() as session:
        api.move_document(session, document_id)


@app.command()
def move_documents(document_type_id: uuid.UUID):
    with get_db() as session:
        api.move_documents(session, document_type_id)
