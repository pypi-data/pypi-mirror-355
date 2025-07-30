import asyncio
import sqlalchemy
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from functools import partial

def do_run_migrations(connection, metadata: sqlalchemy.MetaData):
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(dsn: str, metadata: sqlalchemy.MetaData) -> None:
    connectable = create_async_engine(dsn)
    async with connectable.connect() as connection:
        await connection.run_sync(partial(do_run_migrations, metadata=metadata))
    await connectable.dispose()


def run_migrations_online(dsn: str, metadata: sqlalchemy.MetaData):
    asyncio.run(run_async_migrations(dsn, metadata))