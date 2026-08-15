import logging
import os

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy_utils import create_database, database_exists
from tenacity import retry, stop_after_attempt, wait_fixed

from alembic import command
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine as db_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


def _ensure_sqlite_columns_exist() -> None:
    """
    Inspects all SQLAlchemy models in Base.metadata and ensures missing columns
    are added via ALTER TABLE ADD COLUMN. This prevents 'no such column' errors
    when local SQLite database files are upgraded from older application versions.
    """
    if settings.DATABASE_TYPE != "sqlite":
        return
    try:
        inspector = inspect(db_engine)
        existing_tables = set(inspector.get_table_names())

        with db_engine.begin() as conn:
            for table_name, table in Base.metadata.tables.items():
                if table_name not in existing_tables:
                    continue
                existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(db_engine.dialect)
                        nullable_str = " NULL" if col.nullable else ""
                        default_str = ""
                        if col.default is not None and getattr(
                            col.default, "is_scalar", False
                        ):
                            default_str = f" DEFAULT {col.default.arg!r}"
                        stmt = (
                            f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" '
                            f"{col_type}{nullable_str}{default_str}"
                        )
                        logger.info(
                            f"SQLite auto-migration: Adding missing column "
                            f"'{table_name}.{col.name}' ({col_type})"
                        )
                        conn.execute(text(stmt))
    except Exception as e:
        logger.error(
            f"SQLite auto-column migration check encountered an error: {e}",
            exc_info=True,
        )


def run_db_migrations() -> None:
    """
    Executes Alembic migrations programmatically on app startup.
    For SQLite (desktop/android), also performs auto-column addition as a fallback
    to guarantee existing databases on disk are upgraded without losing data.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

        if os.path.exists(alembic_ini_path):
            logger.info(
                f"Running Alembic database migrations from {alembic_ini_path}..."
            )
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic database migrations completed successfully.")
        else:
            logger.warning(
                f"alembic.ini not found at {alembic_ini_path}. "
                "Skipping Alembic CLI runner."
            )
    except Exception as e:
        logger.warning(
            "Programmatic Alembic migration warning "
            f"(running fallback column check): {e}"
        )

    if settings.DATABASE_TYPE == "sqlite":
        _ensure_sqlite_columns_exist()


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
)
def init() -> None:
    try:
        db_url = str(settings.DATABASE_URL)
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        if not database_exists(engine.url):
            logger.info(f"Database {engine.url.database} does not exist. Creating...")
            create_database(engine.url)
            logger.info("Database created.")
        run_db_migrations()
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()

