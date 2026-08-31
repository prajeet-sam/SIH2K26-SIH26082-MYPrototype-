from __future__ import annotations

from ml.config.settings import Settings, get_settings
from ml.storage.db import make_engine, make_session_factory

_engine = None
_session_factory = None


def get_db():
    global _engine, _session_factory
    settings = get_settings()
    if _engine is None:
        _engine = make_engine(settings)
        _session_factory = make_session_factory(_engine)
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def get_settings_dep() -> Settings:
    return get_settings()
