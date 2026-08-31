from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.db.session import _build_engine

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config(db_url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture()
def migrated_db_url(tmp_path) -> str:
    """Corre las migraciones de Alembic sobre un SQLite descartable y devuelve su URL."""
    db_path = tmp_path / "test_votacion_wg.db"
    db_url = f"sqlite:///{db_path}"
    command.upgrade(_alembic_config(db_url), "head")
    return db_url


@pytest.fixture()
def alembic_config_factory():
    return _alembic_config


@pytest.fixture()
def db_session(migrated_db_url):
    engine = _build_engine(migrated_db_url)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
