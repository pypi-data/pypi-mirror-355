import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, Union
from uuid import UUID

import aiko_services as aiko
from aiko_services import (
    PROTOCOL_PIPELINE,
    ActorTopic,
)
from aiko_services import DataSource as AikoDataSource
from aiko_services import (
    PipelineImpl,
    StreamEvent,
    StreamState,
    compose_instance,
    pipeline_args,
    pipeline_element_args,
)
from pydantic import BaseModel

__all__ = [
    "ActorTopic",
    "Capability",
    "DataSourceCapability",
    "ContextPipelineElement",
    "EntityUUID",
    "PROTOCOL_PIPELINE",
    "PipelineElement",
    "PipelineImpl",
    "StreamEvent",
    "StreamState",
    "compose_instance",
    "compose_instance",
    "pipeline_args",
    "pipeline_element_args",
]

VIDEO = "VIDEO"
TEXT = "TEXT"
IMAGE = "IMAGE"

EntityUUID = UUID

"""Decouple the rest of the code from aiko.PipelineElement"""
ContextPipelineElement = aiko.ContextPipelineElement
PipelineElement = aiko.PipelineElement

# SEPARATOR = b"\x1c"  # ASCII 28 (File Separator)
SEPARATOR = 28  # ASCII 28 (File Separator)


class _BaseCapability:
    class DefaultStreamParameters(BaseModel):
        """Populate with default stream param key fields"""

        pass

    @classmethod
    def default_stream_parameters(cls) -> BaseModel:
        return {
            k: v.default for k, v in cls.DefaultStreamParameters.model_fields.items() if not v.is_required()
        }

    def _get_parameter(
        self, name, default=None, required=False, use_pipeline=True, self_share_priority=True
    ) -> Tuple[Any, bool]:
        """Adds the correct output type to get_parameter type checking
        does not complain
        """
        return self.get_parameter(
            name,
            default=default,
            required=required,
            use_pipeline=use_pipeline,
            self_share_priority=self_share_priority,
        )


class Capability(PipelineElement, _BaseCapability):

    def __init__(self, context: aiko.ContextPipelineElement):
        context.get_implementation("PipelineElement").__init__(self, context)

    def process_frame(self, stream, *args) -> Tuple[StreamEvent, dict]:
        raise NotImplementedError()

    def start_stream(self, stream, stream_id, use_create_frame=True):
        validated_parameters = self.DefaultStreamParameters(**self.parameters)
        for param_name in self.DefaultStreamParameters.model_fields:
            self.parameters[f"{self.definition.name}.{param_name}"] = getattr(
                validated_parameters, param_name
            )
            self.parameters.pop(param_name, None)
        stream.parameters.update(self.parameters)
        return StreamEvent.OKAY, {}


# ToDO: Remove
class DataSourceType(BaseModel):
    # class MediaType(str, Enum):
    #    IMAGE = "IMAGE"
    #    TEXT = "TEXT"
    #    VIDEO = "VIDEO"

    media_type: str
    url: str
    id: UUID
    content: Optional[Any] = None

    @classmethod
    def image_iter(cls, images: Iterable[Union[str, Path, bytes]]):
        pass

    @classmethod
    def video_iter(cls, videos: Iterable[Union[str, Path, bytes]]):
        pass

    @classmethod
    def text_iter(cls, tests: Iterable[Union[str, Path, bytes]]):
        pass


class DataSourceCapability(AikoDataSource, _BaseCapability):

    stream_media_type = None

    class DefaultStreamParameters(_BaseCapability.DefaultStreamParameters):

        rate: Optional[float] = None
        batch_size: int = 1
        data_sources: Optional[str] = None
        file_ids: Optional[Iterable] = None
        task_id: Optional[UUID] = None

    @property
    def rate(self) -> float:
        return self._get_parameter("rate")[0]

    @property
    def batch_size(self) -> int:
        return self._get_parameter("batch_size")[0]

    def __init__(self, context: aiko.ContextPipelineElement):
        context.get_implementation("PipelineElement").__init__(self, context)

    def frame_generator(self, stream, pipeline_iter_idx):
        """Produce a batch of frames.

        Args:
            stream: The Stream context
            pipeline_iter_idx: An integer counting the number of times the
                               pipeline has been executed, (ie: process_frame
                               has been called)

        """
        batch_size = self.batch_size
        task_id, _ = self._get_parameter("task_id")

        frame_data_batch = {"data_files": [], "entities": {}}
        for _ in range(batch_size):
            try:
                data_file, entities = self.get_next_frame_data(stream)
                frame_data_batch["data_files"].append(data_file)
                frame_data_batch["entities"].update(entities)
                self.logger.debug(f"data_file: {data_file}, entities: {entities}")
            except StopIteration:
                pass
            except Exception as e:
                return StreamEvent.ERROR, {"diagnostic": e}

        if not frame_data_batch["data_files"]:
            return StreamEvent.STOP, {"diagnostic": "All frames generated"}

        # For each pipeline iteration the is a batch of file_ids and frame_ids
        stream.variables["task_id"] = task_id

        return StreamEvent.OKAY, frame_data_batch

    def start_stream(self, stream, stream_id):
        stream.variables["video_capture"] = None
        stream.variables["video_frame_generator"] = None

        return super().start_stream(
            stream, stream_id, frame_generator=self.frame_generator, use_create_frame=False
        )

    def get_next_frame_data(self, stream):
        raise NotImplementedError()

    def process_frame(self, stream, data_files, entities) -> Tuple[StreamEvent, Dict]:
        return StreamEvent.OKAY, {"data_files": data_files, "entities": entities}

    def using_hl_data_scheme(self, stream) -> bool:
        return "hl_source_data" in stream.variables
