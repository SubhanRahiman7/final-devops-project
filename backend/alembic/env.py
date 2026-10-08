from sqlalchemy import create_engine, text

from alembic import context
from app import config
from app.database import Base
from app.models import Ticket  # noqa: F401 - registers the table on Base.metadata

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            if connection.dialect.name == "postgresql":
                # replicas start together: only one may migrate at a time
                connection.execute(text("SELECT pg_advisory_xact_lock(2100)"))
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
