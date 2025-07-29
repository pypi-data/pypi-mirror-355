import json
import os
import uuid
from pathlib import Path
from typing import ClassVar, Optional
from uuid import UUID

from sqlalchemy import Column, String, event
from sqlalchemy.orm import Session as SASession
from sqlmodel import Field, Relationship, Session, SQLModel

from highlighter.client.gql_client import HLClient
from highlighter.core.const import HL_ACCOUNTS_DIR, HL_DATA_MODELS_SUB_DIR
from highlighter.core.data_models.account_mixin import AccountMixin
from highlighter.core.data_models.data_file import DataFile
from highlighter.core.utilities import get_slug


# TODO Decide best way to get a session across SDK codebase
class DataFileSource(SQLModel, AccountMixin, table=True):
    data_dir: ClassVar[Optional[Path]] = None

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), sa_column=Column(String, primary_key=True))
    url: str = Field(sa_column=Column(String, default=None, primary_key=True))
    payload: str = Field(sa_column=Column(String, default=None, primary_key=True))
    path_to_response_file: str = Field(sa_column=Column(String, default=None, primary_key=True))
    request_hash: str = Field(sa_column=Column(String, default=None, primary_key=True))
    data_file_id: Optional[UUID] = Field(default=None, foreign_key="datafile.file_id")
    data_file: Optional["DataFile"] = Relationship(back_populates="data_file_sources")

    @classmethod
    def get_data_dir(cls) -> Path:
        if cls.data_dir is None:
            cls.data_dir = (
                HL_ACCOUNTS_DIR
                / HLClient.get_client().account_name
                / HL_DATA_MODELS_SUB_DIR
                / get_slug(cls.__qualname__)
            )
        return cls.data_dir

    @property
    def content(self) -> str:
        """Getter for content"""
        return self._content

    @content.setter
    def content(self, value: str):
        """Setter for content with validation"""
        if not isinstance(value, str):
            raise ValueError("Content must be str")
        self._content = value

    def get_response(self):
        with open(DataFileSource.get_data_dir() / self.path_to_response_file, "r") as file:
            try:
                return json.loads(file.read())
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    f"Error when parsing JSON from cache file contents for DataFileSource: {self.url}, {json.dumps(self.payload)}"
                )


def after_load(target, context):
    """
    Called when an object is loaded from the database
    """
    if not os.path.exists(DataFileSource.get_data_dir() / target.path_to_response_file):
        raise ValueError(f"Error: file on disk not found when loading data_file_source id {target.id}")


event.listen(DataFileSource, "load", after_load)


def before_insert(_mapper, _connection, target):
    """
    Hook method that runs just before inserting a new record
    """
    os.makedirs(os.path.dirname(DataFileSource.get_data_dir() / target.path_to_response_file), exist_ok=True)

    with open(DataFileSource.get_data_dir() / target.path_to_response_file, "w") as file:
        file.write(target.content)


event.listen(DataFileSource, "before_insert", before_insert)


def before_delete(_mapper, connection, target):
    """
    Hook method that runs just before deleting a record
    """
    session = SASession.object_session(target)

    if session is None:
        session = Session(bind=connection)

    if target.path_to_response_file is None:
        raise ValueError("Error: need path_to_response_file to delete data_file_source")

    path_to_response_file = DataFileSource.get_data_dir() / target.path_to_response_file

    if os.path.exists(path_to_response_file):
        os.remove(path_to_response_file)
    else:
        raise ValueError(
            f"Error: no path_to_response_file found when trying to delete data_file_source id {target.id}"
        )


event.listen(DataFileSource, "before_delete", before_delete)
