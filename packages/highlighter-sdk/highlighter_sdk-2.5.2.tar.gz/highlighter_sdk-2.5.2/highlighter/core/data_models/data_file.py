import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Optional
from uuid import UUID

from sqlalchemy import Column, String, event
from sqlalchemy.orm import Session as SASession
from sqlmodel import Field, Relationship, Session, SQLModel, select

from highlighter.client.data_files import get_data_files
from highlighter.client.gql_client import HLClient
from highlighter.core.const import HL_ACCOUNTS_DIR, HL_DATA_MODELS_SUB_DIR
from highlighter.core.data_models.account_mixin import AccountMixin
from highlighter.core.data_models.data_source import DataSource
from highlighter.core.hl_base_model import GQLBaseModel
from highlighter.core.utilities import get_slug, sha512_of_content

logger = logging.getLogger(__name__)


class DataFile(SQLModel, AccountMixin, GQLBaseModel, table=True):
    data_dir: Optional[Path] = None

    file_id: UUID = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content_type: str = Field(sa_column=Column(String))
    recorded_at: datetime = datetime.now()
    media_frame_index: int = 0
    original_source_url: Optional[str] = Field(sa_column=Column(String, default=None))
    file_hash: str = Field(sa_column=Column(String))
    data_file_sources: list["DataFileSource"] = Relationship(back_populates="data_file")
    data_source_uuid: UUID = Field(foreign_key="datasource.uuid")
    data_source: "DataSource" = Relationship(back_populates="data_files")
    _content: Optional[bytes] = None

    def get_data_dir(self) -> Path:
        if self.data_dir is None:
            self.data_dir = (
                HL_ACCOUNTS_DIR
                / HLClient.get_client().account_name
                / HL_DATA_MODELS_SUB_DIR
                / get_slug(DataSource.__qualname__)
                / str(self.data_source_uuid)
                / get_slug(self.__class__.__name__)
            )
        return self.data_dir

    @property
    def content(self) -> bytes | None:
        """Getter for content"""
        return self._content

    @content.setter
    def content(self, value: bytes):
        """Setter for content with validation"""
        if not isinstance(value, bytes):
            raise ValueError("Content must be bytes")
        self._content = value

    def save_to_cloud(self):
        if self.original_source_url is None or self.original_source_url == "":
            raise ValueError("Error: need original_source_url to save file to cloud")

        if self.data_source_uuid is None:
            raise ValueError("Error: need data_source_uuid to save file to cloud")

        from highlighter.client import HLClient
        from highlighter.client.data_files import create_data_file

        now = datetime.now(timezone.utc).astimezone()
        timezone_name = now.tzname()
        hl_client = HLClient.get_client()

        response = create_data_file(
            hl_client,
            data_file_path=self.path_to_content_file,
            data_source_uuid=self.data_source_uuid,
            observed_timezone=timezone_name,
            recorded_at=now.isoformat(),
            uuid=str(self.file_id),
        )

        logger.info(f"DataFile saved to cloud with id {self.file_id} with response {response}")

        return response

    @property
    def path_to_content_file(self):
        if self.original_source_url is None:
            raise ValueError(f"Error: data file with ID {self.file_id} has no original_source_url")
        else:
            return self.get_data_dir() / self.original_source_url

    def write_content_to_disk(self):
        os.makedirs(os.path.dirname(self.path_to_content_file), exist_ok=True)

        if os.path.exists(self.path_to_content_file):
            raise ValueError(f"Error: path to content file already exists for data file {self.file_id}")

        if self.content is None:
            raise ValueError(
                f"Error: trying to write content to disk and content is None for data file {self.file_id}"
            )

        with open(self.path_to_content_file, "wb") as file:
            file.write(self.content)


# TODO We can't always rely on getting session from connection
# More reliable way is to use `before_flush` hook then check if is insert, update, delete etc
def before_insert(_mapper, connection, target):
    """
    Hook method that runs just before inserting a new record
    """
    session = SASession.object_session(target)

    if session is None:
        session = Session(bind=connection)

    if target.original_source_url is None:
        raise ValueError("Error: need original_source_url to save data_file")

    if target.content is None:
        raise ValueError("DataFile content must be set before insertion")
    file_hash = sha512_of_content(target.content)
    statement = select(DataFile).filter_by(file_hash=file_hash, data_source_uuid=target.data_source_uuid)
    results = session.exec(statement).all()

    if len(results) > 0:
        raise ValueError(
            f"Error: existing data_file ID(s) '{', '.join([str(df.file_id) for df in results])}' found by file_hash '{file_hash}' in agent database for data_source '{target.data_source_uuid}'"
        )

    hl_client = HLClient.get_client()
    existing_data_source_data_files = list(
        get_data_files(hl_client, file_hash=[file_hash], data_source_uuid=[str(target.data_source_uuid)])
    )

    if existing_data_source_data_files != []:
        if (
            len(existing_data_source_data_files) > 1
            or existing_data_source_data_files[0].uuid != target.file_id
        ):
            raise ValueError(
                f"Error: file_hash {file_hash} already exists in Highlighter cloud in data_source_uuid {target.data_source_uuid} for data file ID(s) {', '.join([data_file.id for data_file in existing_data_source_data_files])}"
            )

    target.file_hash = file_hash


event.listen(DataFile, "before_insert", before_insert)


def before_delete(_mapper, connection, target):
    """
    Hook method that runs just before deleting a record
    """
    if os.path.exists(target.path_to_content_file):
        os.remove(target.path_to_content_file)


event.listen(DataFile, "before_delete", before_delete)
