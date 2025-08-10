import sys
from logging.config import fileConfig
from os.path import abspath, dirname

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db.base_class import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the project's root directory to the Python path
# This allows alembic to find the app modules
sys.path.insert(0, dirname(dirname(abspath(__file__))))

# --- Model Imports ---
# All application models are imported here for Alembic's 'autogenerate'
# support to detect schema changes.
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.models.import_session import ImportSession
from app.models.parsed_transaction import ParsedTransaction
from app.models.asset_alias import AssetAlias
# ---------------------

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Set the sqlalchemy.url from our application settings object
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
