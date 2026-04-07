from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from nssp_v2.shared.config import get_settings


class Base(DeclarativeBase):
    pass


# Engine lazy: non viene creato a import-time, ma alla prima chiamata di get_engine().
# Questo evita che l'import di db.py in test unit (es. per Base o i modelli) tenti
# di risolvere la config prima che l'ambiente di test sia pronto.
_engine = None


def get_engine():
    """Restituisce l'engine SQLAlchemy singleton, creandolo alla prima chiamata."""
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url)
    return _engine


def SessionLocal() -> Session:
    """Restituisce una Session pronta per l'uso come context manager.

    Uso tipico:
        with SessionLocal() as session:
            ...
    """
    return Session(get_engine())


def get_session():
    """FastAPI dependency: yields a database session."""
    with Session(get_engine()) as session:
        yield session
