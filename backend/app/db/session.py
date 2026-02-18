from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

resolved_db_url = settings.resolved_database_url()
sqlite_connect_args = {"check_same_thread": False} if resolved_db_url.startswith("sqlite") else {}
engine = create_engine(resolved_db_url, echo=False, connect_args=sqlite_connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
