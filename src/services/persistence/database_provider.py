from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from src.utils.services.aws.appconfig_service import get_config_service
from src.services.persistence.models import Base
from src.services.persistence.repositories.history_repository import HistoryRepository
from src.utils.singleton import Singleton


class DatabaseProvider(metaclass=Singleton):
    """Provides database connections and repository access."""

    def __init__(self):
        config = get_config_service()
        user = config.get("mysql.user")
        password = config.get("mysql.password")
        host = config.get("mysql.host")
        port = config.get("mysql.port")
        db_name = config.get("mysql.database")

        dsn = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

        self._engine = create_engine(dsn, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self._engine)

        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def history_repository(self) -> Generator[HistoryRepository, None, None]:
        with self.session() as session:
            yield HistoryRepository(session)

    def is_healthy(self) -> bool:
        try:
            with self.session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
