import uuid

import typer

from path_tmpl_worker import api
from path_tmpl_worker.db.engine import Session

app = typer.Typer(help="CLI for Path Template worker")


@app.command()
def move_document(document_id: uuid.UUID):
    with Session() as db_session:
        api.move_document(db_session, document_id)


@app.command()
def move_documents(document_type_id: uuid.UUID):
    with Session as db_session:
        api.move_documents(db_session, document_type_id)
