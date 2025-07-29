import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

import numpy as np
from PIL import Image
from pydantic import ConfigDict

from highlighter.core.decorators import deprecated_class

from ...core import HLDataModel, draw_annotations_on_image, resize_image

__all__ = ["DataFile"]

warnings.simplefilter("always", DeprecationWarning)  # Force showing deprecation warnings


@deprecated_class
class DataFile(HLDataModel):
    file_id: Optional[UUID] = None
    content_type: str
    content: Any
    recorded_at: datetime = datetime.now()
    media_frame_index: int = 0
    original_source_url: Optional[str] = None

    @classmethod
    def from_image(
        cls,
        content: Union[np.ndarray, Image.Image, str, Path],
        file_id: UUID,
        media_frame_index: int = 0,
        original_source_url: Optional[str] = None,
    ):
        if isinstance(content, (str, Path)):
            content = Image.open(content)

        assert isinstance(content, (np.ndarray, Image.Image))

        return cls(
            file_id=file_id,
            content_type="image",
            content=content,
            media_frame_index=media_frame_index,
            original_source_url=original_source_url,
        )

    def get_id(self) -> UUID:
        return self.file_id

    def resize(self, width: int, height: int) -> "DataFile":
        assert self.content_type == "image"
        self.content = resize_image(self.content, width=width, height=height)
        return self

    def draw_annotations(self, annotations: "Annotations"):
        overlay = draw_annotations_on_image(self.content, annotations)
        return overlay

    class ContentTypeEnum(Enum):
        UNKNOWN = "unknown"
        IMAGE = "image"
        VIDEO = "video"
        TEXT = "text"
        JSON = "json"
        AUDIO = "audio"
        WEB_PAGE = "web_page"
        KML = "kml"
