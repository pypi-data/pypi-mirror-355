import os

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from highlighter.core.const import HL_AGENTS_SUB_DIR, HL_DIR

__all__ = [
    "Database",
    "HIGHLIGHTER_DATA_DIR",
    "HIGHLIGHTER_PATH_TO_DATABASE_FILE",
]


HIGHLIGHTER_DATA_DIR = HL_DIR / HL_AGENTS_SUB_DIR / "data"
HIGHLIGHTER_PATH_TO_DATABASE_FILE = HL_DIR / HL_AGENTS_SUB_DIR / "db" / "database.sqlite"


class Database:
    """The Highlighter agent database"""

    engine: Engine = create_engine(
        f"sqlite:///{HIGHLIGHTER_PATH_TO_DATABASE_FILE}", connect_args={"check_same_thread": False}
    )

    def __init__(self):
        os.makedirs(os.path.dirname(HIGHLIGHTER_PATH_TO_DATABASE_FILE), exist_ok=True)
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)
