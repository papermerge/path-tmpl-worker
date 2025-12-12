import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

SQLALCHEMY_DATABASE_URL = os.environ.get("PAPERMERGE__DATABASE__URL")
connect_args = {}
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
    "postgresql://", "postgresql+syncpg://", 1
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args, poolclass=NullPool
)

Session = sessionmaker(engine, expire_on_commit=False)


def get_engine():
    return engine
