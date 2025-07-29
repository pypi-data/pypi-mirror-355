import json
from datetime import datetime, timedelta
from enum import Enum
from logging import warning
from os import PathLike
from pathlib import Path
from typing import Generator, List, Optional
from urllib.parse import urlparse

from highlighter.cli.logging import get_default_logger

try:
    import cv2
except ModuleNotFoundError as _:
    cv2 = None

import numpy as np
from PIL import Image

from highlighter.agent.capabilities.base_capability import IMAGE, TEXT, VIDEO
from highlighter.client import download_bytes
from highlighter.client.base_models import DataFile
from highlighter.client.io import (
    _pil_open_image_bytes,
    _pil_open_image_path,
    _pil_open_image_url,
)
from highlighter.core.exceptions import require_package

from .base_capability import DataSourceCapability

__all__ = [
    "ImageDataSource",
    "TextDataSource",
    "JsonArrayDataSource",
    "VideoDataSource",
]


def _iter_buffer(
    buffer,
    sep: bytes,
) -> Generator[bytes, None, None]:
    """
    Streams data from stdin until the Nth occurrence of a separator byte sequence.

    sep: The separator byte sequence (e.g., b'\n' or b'\x00\x01')
    """
    if sep is None or len(sep) == 0:
        raise ValueError("Separator must be a non-empty bytes object")

    byte_result = bytearray()
    buffer_remainder = bytearray()

    while True:
        chunk = buffer.read(4096)  # Adjusted for testing, increase for performance
        if not chunk:
            if byte_result:
                byte_result = bytes(byte_result)
                yield byte_result
            break

        buffer_remainder.extend(chunk)

        while True:
            sep_index = buffer_remainder.find(sep)
            if sep_index == -1:
                break

            byte_result.extend(buffer_remainder[:sep_index])
            yield bytes(byte_result)

            byte_result.clear()
            buffer_remainder = buffer_remainder[sep_index + len(sep) :]

        byte_result.extend(buffer_remainder)
        buffer_remainder.clear()


class TextFrameIterator:

    def __init__(
        self,
        source_buffers=None,
        source_urls=None,
        logger=None,
    ):

        self.logger = logger if logger is not None else get_default_logger("TextFrameIterator")
        self.source_buffers = source_buffers
        self.source_urls = source_urls

        if self.source_urls is not None:
            self.logger.info("TextFrameIterator using source_url")
            self._source = iter([str(u) for u, _ in self.source_urls])
        elif self.source_buffers is not None:

            def iter_buffers(bufs):
                for b in bufs:
                    for item in _iter_buffer(b, "===END===".encode("utf-8")):
                        yield item.decode()

            self._source = iter_buffers(self.source_buffers)
            self.logger.info(f"TextFrameIterator using source_buffer")
        else:
            raise ValueError("Must provide source_buffer &| source_url")

        self.frame_index = 0

    def _is_url(self, p):
        return all([urlparse(p), urlparse(p).netloc])

    def _is_local_path(self, p):
        return Path(p).exists()

    def _read_text(self, text_src):
        if self._is_local_path(text_src):
            with open(text_src, "r") as f:
                text = f.read()
            original_source_url = text_src
        elif self._is_url(text_src):
            text = download_bytes(text_src).decode("utf-8")
            original_source_url = text_src
        else:
            text = text_src
            original_source_url = None
        return text, original_source_url

    def __iter__(self):
        return self

    def __next__(self):
        text_src = next(self._source)
        text_content, original_source_url = self._read_text(text_src)

        data_file = DataFile(
            # file_id=self.ds.id,
            content=text_content,
            content_type="text",
            media_frame_index=0,
            original_source_url=original_source_url,
        )
        return data_file


class TextDataSource(DataSourceCapability):
    """

    TODO: Check/update this

    Example:
        # process a single string
        hl agent start --data-source TextDataSource PIPELINE.json "tell me a joke."

        # process many text files
        ToDo

        # Read from stdin
        cat file | hl agent start --data-source TextDataSource -sp read_stdin=true PIPELINE.json
    """

    stream_media_type = TEXT

    class DefaultStreamParameters(DataSourceCapability.DefaultStreamParameters):
        byte_encoding: Optional[str] = "utf-8"

    @property
    def byte_encoding(self) -> str:
        value, _ = self._get_parameter("byte_encoding")
        return value

    def get_text_frame_generator(self, stream):

        if "source_paths_generator" in stream.variables:
            for frame_data in TextFrameIterator(
                source_buffers=None,
                source_urls=stream.variables["source_paths_generator"],
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in TextFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_frame_data(self, stream):

        frame_generator = stream.variables.get("text_frame_generator", None)
        if frame_generator is None:
            frame_generator = self.get_text_frame_generator(stream)
            stream.variables["text_frame_generator"] = frame_generator

        data_file = next(frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_file, entities


class JsonArrayFrameIterator:

    def __init__(self, source_buffers=None, source_urls=None, key="", logger=None):

        self.logger = logger if logger is not None else get_default_logger("JsonArrayFrameIterator")
        self.source_urls = source_urls
        self.source_buffers = source_buffers
        self.key = key

        if self.source_urls is not None:
            self.logger.info("Using source_urls")
            self._source = self._iter_source_urls(self.source_urls)

        elif self.source_buffers is not None:
            self.logger.info("Using source_buffers")
            self._source = self._iter_source_buffers(self.source_buffers)
        else:
            raise ValueError("Must provide source_buffer &| source_url")

    def _is_url(self, p):
        return all([urlparse(p), urlparse(p).netloc])

    def _is_local_path(self, p):
        return Path(p).exists()

    def _iter_source_urls(self, source_urls):
        frame_counter = 0
        for url in source_urls:
            url = str(url)
            if self._is_url(url):
                arr = json.loads(download_bytes(url).decode("utf-8"))
            elif self._is_local_path(url):
                with open(url, "r") as f:
                    arr = json.load(f)
            else:
                raise ValueError(f"Unable to load {url} as json")

            for k in self.key.split("."):
                arr = arr[k]

            for item in arr:
                yield item, url, frame_counter
                frame_counter += 1

    def _iter_source_buffers(self, source_buffers):
        frame_counter = 0
        for buf in source_buffers:
            for item in _iter_buffer(buf, "===END===".encode("utf-8")):
                arr = json.loads(item)

                for k in self.key.split("."):
                    arr = arr[k]

                for item in arr:
                    yield item, None, frame_counter
                    frame_counter += 1

    def __iter__(self):
        return self

    def __next__(self):

        content, original_source_url, frame_index = next(self._source)
        data_file = DataFile(
            # file_id=self.ds.id,
            content=content,
            content_type="text",
            media_frame_index=frame_index,
            original_source_url=original_source_url,
        )
        return data_file


class JsonArrayDataSource(DataSourceCapability):

    stream_media_type = TEXT

    class DefaultStreamParameters(DataSourceCapability.DefaultStreamParameters):
        key: str = ""

    @property
    def key(self) -> str:
        value, _ = self._get_parameter("key")
        return value

    def get_json_array_frame_generator(self, stream):

        if "source_paths_generator" in stream.variables:
            source_urls = [path for path, _ in stream.variables["source_paths_generator"]]
            for frame_data in JsonArrayFrameIterator(
                source_buffers=None,
                source_urls=source_urls,
                key=self.key,
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in JsonArrayFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                key=self.key,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_frame_data(self, stream):

        json_array_frame_generator = stream.variables.get("json_array_frame_generator", None)
        if json_array_frame_generator is None:
            json_array_frame_generator = self.get_json_array_frame_generator(stream)
            stream.variables["json_array_frame_generator"] = json_array_frame_generator

        data_file = next(json_array_frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_file, entities


class OutputType(str, Enum):
    numpy = "numpy"
    pillow = "pillow"


class ImageFrameIterator:
    def __init__(
        self,
        source_buffers=None,
        source_urls=None,
        output_type: OutputType = OutputType.numpy,
        logger=None,
    ):

        self.logger = logger if logger is not None else get_default_logger("ImageFrameIterator")
        self.source_buffers = source_buffers
        self.source_urls = source_urls
        self.output_type = output_type

        if self.source_urls is not None:
            self.logger.info("ImageFrameIterator using source_url")
            self._source = iter([str(u) for u, _ in self.source_urls])
        elif self.source_buffers is not None:

            def iter_buffers(bufs):
                for b in bufs:
                    for item in _iter_buffer(b, "===END===".encode("utf-8")):
                        yield item

            self._source = iter_buffers(self.source_buffers)
            self.logger.info(f"ImageFrameIterator using source_buffer")
        else:
            raise ValueError("Must provide source_buffer &| source_url")

        self.frame_index = 0

    def _is_url(self, p):
        return all([urlparse(p), urlparse(p).netloc])

    def _is_local_path(self, p):
        return Path(p).exists()

    def __iter__(self):
        return self

    def _read_image(self, img_src):
        if isinstance(img_src, str) and self._is_local_path(img_src):
            img = _pil_open_image_path(img_src)
            original_source_url = img_src
        elif isinstance(img_src, str) and self._is_url(img_src):
            img = _pil_open_image_url(img_src)
            original_source_url = img_src
        else:
            img = _pil_open_image_bytes(img_src)
            original_source_url = None
        return img, original_source_url

    def __next__(self):
        img_src = next(self._source)
        img, original_source_url = self._read_image(img_src)

        if self.output_type == OutputType.numpy:
            img = np.array(img, dtype=np.uint8)

        data_file = DataFile(
            # file_id=self.ds.id,
            content=img,
            content_type="image",
            media_frame_index=0,
            original_source_url=original_source_url,
        )
        return data_file


class ImageDataSource(DataSourceCapability):
    """

    Example:
        # process a single image
        hl agent start PIPELINE.json image.jpg

        # process many images
        find image/dir/ -n "*.jpg" | hl agent start PIPELINE.json
    """

    stream_media_type = IMAGE

    class DefaultStreamParameters(DataSourceCapability.DefaultStreamParameters):
        output_type: OutputType = OutputType.numpy

    @property
    def output_type(self) -> OutputType:
        value, _ = self._get_parameter("output_type")
        return value

    def get_image_frame_generator(self, stream):

        if "source_paths_generator" in stream.variables:
            for frame_data in ImageFrameIterator(
                source_buffers=None,
                source_urls=stream.variables["source_paths_generator"],
                output_type=self.output_type,
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in ImageFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                output_type=self.output_type,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_frame_data(self, stream):

        frame_generator = stream.variables.get("image_frame_generator", None)
        if frame_generator is None:
            frame_generator = self.get_image_frame_generator(stream)
            stream.variables["image_frame_generator"] = frame_generator

        data_file = next(frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_file, entities


@require_package(cv2, "cv2", "opencv")
class VideoFrameIterator:

    def __init__(
        self, source_buffers=None, source_urls=None, output_type: OutputType = OutputType.numpy, logger=None
    ):

        self.logger = logger if logger is not None else get_default_logger("VideoFrameIterator")
        self.output_type = output_type
        self.source_urls = source_urls
        self.source_buffers = source_buffers
        self.start_time = datetime.now()
        self.frame_index = 0

        if self.source_urls is not None:
            self.logger.info("Using VideoCapture")
            self._source = iter([str(u) for u in self.source_urls])
            self._cap_cls = cv2.VideoCapture

        elif self.source_buffers is not None:
            from highlighter.agent.capabilities._buffered_video_reader import (
                BufferedVideoCapture,
            )

            self.logger.info("Using BufferedVideoCapture")
            self._source = iter(self.source_buffers)
            self._cap_cls = BufferedVideoCapture
        else:
            raise ValueError("Must provide source_buffer &| source_url")

        self._cap, self._original_source_url = self._init_video_capture()

    def _init_video_capture(self):
        src = next(self._source)
        _cap = self._cap_cls(src)
        if not _cap.isOpened():
            raise ValueError("Cannot open video file or buffer")
        if isinstance(src, str):
            _original_source_url = src
        else:
            _original_source_url = None
        return _cap, _original_source_url

    def __iter__(self):
        return self

    def __next__(self):

        ret, frame_img = self._cap.read()
        if not ret:  # No more frames to read
            self._cap.release()
            self._cap, self._original_source_url = self._init_video_capture()
            ret, frame_img = self._cap.read()
            if not ret:
                self._cap.release()
                raise StopIteration

        frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)

        if self.output_type == OutputType.pillow:
            frame_img = Image.fromarray(frame_img)

        timestamp = self._cap.get(cv2.CAP_PROP_POS_MSEC)
        data_file = DataFile(
            # file_id=self.ds.id,
            content=frame_img,
            content_type="image",
            recorded_at=self.start_time + timedelta(milliseconds=timestamp),
            media_frame_index=self.frame_index,
            original_source_url=self._original_source_url,
        )
        self.frame_index += 1
        return data_file

    def __del__(self):
        if self._cap.isOpened():
            self._cap.release()

    def get_total_frames(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def extract_frames_by_id(
        self, frame_ids: List[int], frame_save_dir: PathLike, filename: str
    ) -> List[int]:
        if len(frame_ids) == 0:
            return []

        frame_ids = sorted(frame_ids, reverse=True)

        total_frames = self.get_total_frames()
        invalid_ids = [fid for fid in frame_ids if fid < 0 or fid >= total_frames]
        if invalid_ids:
            warning(f"These frame IDs are invalid (out of range 0-{total_frames-1}): {invalid_ids}")
            frame_ids = [fid for fid in frame_ids if fid >= 0 and fid < total_frames]

        extracted_frame_ids = []
        frame_id = frame_ids.pop()
        _frame_save_dir = Path(frame_save_dir)
        _frame_save_dir.mkdir(parents=True, exist_ok=True)
        for frame in self:
            if frame.media_frame_index == frame_id:
                save_path = _frame_save_dir / filename.format(frame_id)
                Image.fromarray(frame.content).save(save_path)
                extracted_frame_ids.append(frame_id)
                if frame_ids:
                    frame_id = frame_ids.pop()
                else:
                    break
        return extracted_frame_ids


class VideoDataSource(DataSourceCapability):

    stream_media_type = VIDEO

    class DefaultStreamParameters(DataSourceCapability.DefaultStreamParameters):
        output_type: OutputType = OutputType.numpy

    @property
    def output_type(self) -> OutputType:
        value, _ = self._get_parameter("output_type")
        return value

    def get_video_frame_generator(self, stream):

        if "source_paths_generator" in stream.variables:
            source_urls = [path for path, task_id in stream.variables["source_paths_generator"]]
            for frame_data in VideoFrameIterator(
                source_buffers=None,
                source_urls=source_urls,
                output_type=self.output_type,
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in VideoFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                output_type=self.output_type,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_frame_data(self, stream):

        video_frame_generator = stream.variables.get("video_frame_generator", None)
        if video_frame_generator is None:
            video_frame_generator = self.get_video_frame_generator(stream)
            stream.variables["video_frame_generator"] = video_frame_generator

        data_file = next(video_frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_file, entities
