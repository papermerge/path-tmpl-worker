from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from path_tmpl_worker.config import get_settings


@lru_cache()
def get_engine(url: str | None = None):
    settings = get_settings()

    if url is None:
        SQLALCHEMY_DATABASE_URL = settings.papermerge__database__url
    else:
        SQLALCHEMY_DATABASE_URL = url

    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=NullPool,
    )
