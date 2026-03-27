import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from common.logging_config import get_logger


load_dotenv()
logger = get_logger(__name__)

REQUIRED_DB_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def _get_db_settings():
    settings = {key: os.getenv(key) for key in REQUIRED_DB_VARS}
    missing = [key for key, value in settings.items() if not value]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Missing required database environment variables: {missing_str}")
    return settings


def get_database_url():
    settings = _get_db_settings()
    return (
        f"postgresql://{settings['DB_USER']}:{settings['DB_PASSWORD']}"
        f"@{settings['DB_HOST']}:{settings['DB_PORT']}/{settings['DB_NAME']}"
    )


def get_engine():
    connection_string = get_database_url()
    connect_args = {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10"))}
    sslmode = os.getenv("DB_SSLMODE")
    if sslmode:
        connect_args["sslmode"] = sslmode

    return create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        connect_args=connect_args,
    )


def test_connection():
    try:
        engine = get_engine()
        with engine.connect():
            logger.info("Database connection successful.")
    except Exception:
        logger.exception("Database connection failed.")
        raise


if __name__ == "__main__":
    test_connection()
