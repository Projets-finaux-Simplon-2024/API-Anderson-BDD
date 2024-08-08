from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlalchemy import create_engine
import os

config = context.config

fileConfig(config.config_file_name)

from app.database import Base
from app.models import User, Role, Collection, Document, Chunk
target_metadata = Base.metadata

def get_database_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

def run_migrations_offline():
    url = get_database_url()
    if url is None:
        raise ValueError("No URL configured for the database. Please check the alembic.ini file or the DATABASE_URL environment variable.")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = get_database_url()
    if url is None:
        raise ValueError("No URL configured for the database. Please check the alembic.ini file or the DATABASE_URL environment variable.")
    connectable = create_engine(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
