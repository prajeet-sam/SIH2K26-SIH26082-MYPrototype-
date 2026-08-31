from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ml.config.settings import Settings


def make_engine(settings: Settings) -> Engine:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", "", 1))
        if db_path.parent and str(db_path.parent) not in ("", "."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    else:
        engine = create_engine(url, pool_pre_ping=True, future=True)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_schema(engine: Engine) -> None:
    from ml.storage.models import Base

    Base.metadata.create_all(engine)


def table_counts(engine: Engine) -> dict[str, int]:
    tables = [
        "stations",
        "pollution_observations",
        "weather_observations",
        "features",
        "data_quality_logs",
        "forecasts",
    ]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            exists = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                {"t": t},
            ).fetchone()
            if exists is not None or not engine.dialect.name == "sqlite":
                try:
                    counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
                except Exception:
                    counts[t] = -1
    return counts
