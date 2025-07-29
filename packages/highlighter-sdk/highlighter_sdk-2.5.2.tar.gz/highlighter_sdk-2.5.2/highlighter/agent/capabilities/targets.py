import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from highlighter.client.utilities import replace_forward_slash_with_underscore
import numpy as np
from PIL import Image

from highlighter import DatumSource
from highlighter.client import HLJSONEncoder
from highlighter.client.base_models.data_file import DataFile
from highlighter.client.base_models.entity import Entity
from highlighter.client.base_models.observation import Observation
from highlighter.core import LabeledUUID

from .base_capability import (
    Capability,
    ContextPipelineElement,
    DataSourceType,
    StreamEvent,
)

__all__ = [
    "EntityWriteFile",
    "WriteStdOut",
    "ImageWriteStdOut",
    "ImageWrite",
    "TextToStdout",
]

# ToDo: The attribute(s) returned by an llm or any model
#       will need to be configured at run time. The the exception
#       of a hand-full of attributes (pixel-location, object-class, ...)
#       we can't know ahead of time what attribute the output of
#       the model will represent.
TEXT_ATTRIBUTE_UUID = LabeledUUID(int=2, label="response")


class BaseEntityWrite(Capability):

    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        task_id: str = ""

    def __init__(self, context: ContextPipelineElement):
        super().__init__(context)
        self.frame_entities = dict()

    def get_task_id(self, stream) -> str:
        return stream.variables.get("task_id", None)

    def _get_source_file_location(self, stream):
        # ToDo: Find a better palce to put/get this from
        #       see also, ImageDataSource.process_frame
        source_info = stream.variables.get("source_info", {})
        source_file_location = source_info.get("source_file_location", None)
        if source_file_location is not None:
            return Path(source_file_location)
        return None

    def on_per_frame(self, stream, entities, data_file):
        pass

    def process_frame(
        self, stream, data_files: List[DataFile], entities: List[Dict[UUID, Entity]]
    ) -> Tuple[StreamEvent, dict]:
        for frame_entities, data_file in zip(entities, data_files):
            self.on_per_frame(stream, frame_entities, data_file)
        self.frame_entities[stream.frame_id] = entities
        return StreamEvent.OKAY, {}

    def on_stop_stream(self, stream, stream_id, entities):
        """Note this will not be called if you're calling `pipeline.process_frame`
        directly. Because this is called when a stream is stopped
        """
        pass

    def stop_stream(self, stream, stream_id) -> Tuple[StreamEvent, Optional[Dict]]:
        self.on_stop_stream(stream, stream_id, self.frame_entities)
        return StreamEvent.OKAY, {}


class EntityWriteFile(BaseEntityWrite):

    class DefaultStreamParameters(BaseEntityWrite.DefaultStreamParameters):
        """Can contain the following placeholders:

            {frame_id}
            {task_id}
            {timestamp}

        for example:
            per_frame_output_file = 'output_{frame_id}_{timestamp}.json'
        """

        per_frame_output_file: Optional[str] = None

        """Can contain the following placeholders:

            {task_id}
            {timestamp}
        """
        stop_stream_output_file: Optional[str] = None

    @property
    def per_frame_output_file(self) -> Optional[str]:
        value, _ = self._get_parameter("per_frame_output_file", None)
        return value

    @property
    def stop_stream_output_file(self) -> Optional[str]:
        value, _ = self._get_parameter("stop_stream_output_file", None)
        return value

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d%H%M%S%f")

    def get_per_frame_output_file_path(self, stream, data_file):
        task_id = stream.stream_id
        frame_id = data_file.media_frame_index

        return self.per_frame_output_file.format(
            frame_id=frame_id,
            task_id=task_id,
            timestamp=self._timestamp(),
        )

    def on_per_frame(self, stream, entities, data_file):
        if self.per_frame_output_file:
            output_file_path = self.get_per_frame_output_file_path(stream, data_file)
            Path(output_file_path).parent.mkdir(exist_ok=True, parents=True)
            output_str = json.dumps(entities, indent=2, sort_keys=True, cls=HLJSONEncoder)
            with open(output_file_path, "w") as f:
                f.write(output_str)
                self.logger.debug(f"{self.my_id()}: wrote {len(entities)} entities to {output_file_path} ")

    def get_on_stop_stream_output_file_path(self, stream):
        task_id = stream.variables.get("task_id", None)
        return self.stop_stream_output_file.format(
            stream_id=stream.stream_id,
            task_id=task_id,
        )

    def on_stop_stream(self, stream, stream_id, all_entities):
        if self.stop_stream_output_file:
            self.logger.debug(f"Writing stop_stream_output_file: {self.stop_stream_output_file}")
            output_file_path = self.get_on_stop_stream_output_file_path(stream)
            Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(json.dumps(all_entities, indent=2, sort_keys=True, cls=HLJSONEncoder))


class WriteStdOut(BaseEntityWrite):

    def on_per_frame(self, stream, entities, data_files):

        for entity in entities:
            output = {"frame_data": entity, "frame_id": stream.frame_id}
            print(json.dumps(output), file=sys.stdout, cls=HLJSONEncoder)


class ImageWriteStdOut(Capability):

    def process_frame(self, stream, data_files: List[DataSourceType]) -> Tuple[StreamEvent, Optional[Dict]]:
        image = data_files[0].content
        output_buffer = io.BytesIO()
        if isinstance(image, np.ndarray):
            Image.fromarray(image).save(output_buffer, format="PNG")
        elif isinstance(image, Image.Image):
            image.save(output_buffer, format="PNG")

        sys.stdout.buffer.write(output_buffer.getvalue())

        return StreamEvent.OKAY, {}


class ImageWrite(Capability):

    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        output_dir: str

        # Can use placeholders, {file_id}, {media_frame_index}, {original_source_url}
        output_pattern: str

    @property
    def output_dir(self) -> str:
        value, _ = self._get_parameter("output_dir")
        return value

    @property
    def output_pattern(self) -> str:
        value, _ = self._get_parameter("output_pattern")
        return value

    def process_frame(self, stream, data_files: List[DataSourceType]) -> Tuple[StreamEvent, dict]:
        output_dir = Path(self.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        for df in data_files:
            filename = self.output_pattern.format(
                file_id=df.file_id,
                media_frame_index=df.media_frame_index,
                original_source_url=df.original_source_url,
            )
            dest = output_dir / filename
            image = df.content
            if isinstance(image, np.ndarray):
                Image.fromarray(image).save(dest)
            elif isinstance(image, Image.Image):
                image.save(dest)

        return StreamEvent.OKAY, {}


class TextToStdout(Capability):
    def process_frame(self, stream, text: str) -> Tuple[StreamEvent, Union[Dict, str]]:
        sys.stdout.write(text)
        # sys.stdout.write(chr(28))  # ASCII 28 (Record Separator)
        sys.stdout.flush()
        return StreamEvent.OKAY, {}


class TextToFile(Capability):
    def start_stream(self, stream, stream_id, use_create_frame=True):
        self.path_to_write_files, _ = self._get_parameter("path_to_write_files", required=True)

        if not os.path.exists(self.path_to_write_files):
            os.makedirs(self.path_to_write_files)

        self.file_suffix, _ = self._get_parameter("file_suffix", required=True)

        return super().start_stream(stream, stream_id, use_create_frame)

    def process_frame(self, stream, text: str) -> Tuple[StreamEvent, Union[Dict, str]]:
        parsed_text = json.loads(text)
        company_name = replace_forward_slash_with_underscore(parsed_text["company_name"])
        path_to_file = Path(self.path_to_write_files) / f"{company_name}.{self.file_suffix}"

        with open(path_to_file, "w") as file:
            file.write(text)

        return StreamEvent.OKAY, {"text": text}


class TextFilesToCsvFile(Capability):
    def start_stream(self, stream, stream_id, use_create_frame=True):
        self.path_to_output_file, _ = self._get_parameter("path_to_output_file", required=True)

        path = os.path.dirname(self.path_to_output_file)

        if not os.path.exists(path):
            os.makedirs(path)

        self.data = []

        return super().start_stream(stream, stream_id, use_create_frame)

    def process_frame(self, stream, data_files: List[DataFile]) -> Tuple[StreamEvent, Union[Dict, str]]:
        text_content = data_files[0].content
        parsed_text = json.loads(text_content)

        self.data.append(parsed_text)

        return StreamEvent.OKAY, {"text": text_content}

    def stop_stream(self, stream, stream_id):
        with open(self.path_to_output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.data[0].keys())
            writer.writeheader()
            writer.writerows(self.data)

        logger.info(f"CSV written to {self.path_to_output_file}")

        return StreamEvent.OKAY, {}
