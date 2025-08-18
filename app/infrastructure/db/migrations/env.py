from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio
import os
import sys

# Ajouter chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from app.infrastructure.db.base import Base
from app.domain.entities.user import User
from app.domain.entities.auth_provider import AuthProvider
from app.config import settings

import app.domain.entities.user
import app.domain.entities.role
import app.domain.entities.invitation
import app.domain.entities.verification_code
import app.domain.entities.user_resume
import app.domain.entities.user_skill
import app.domain.entities.user_score
import app.domain.entities.black_listed_token
import app.domain.entities.password_reset_token

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = settings.database_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
