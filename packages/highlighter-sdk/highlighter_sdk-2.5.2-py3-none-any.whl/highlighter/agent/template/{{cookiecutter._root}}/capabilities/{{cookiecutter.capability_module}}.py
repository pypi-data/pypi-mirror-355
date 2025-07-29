from typing import Dict, List, Optional, Tuple, Union

from highlighter.agent.capabilities import Capability, StreamEvent
from highlighter.client import DataFile
from highlighter.core import LabeledUUID

__all__ = ["{{cookiecutter.capability_class_name}}"]

ATTRIBUTE_UUID = LabeledUUID(int=2, label="response")

class {{cookiecutter.capability_class_name}}(Capability):
    """Does something cool
    """

    def __init__(self, context):
        context.get_implementation("PipelineElement").__init__(self, context)

    def start_stream(self, stream, stream_id) -> Tuple[StreamEvent, Optional[str]]:
        return StreamEvent.OKAY, None

    {% if cookiecutter.data_type == 'text' -%}
    def process_frame(self, stream, data_files: List[DataFile]) -> Tuple[StreamEvent, Union[Dict, str]]:
        for df in data_files:
            self.logger.info(f"DataFile.content: {df.content}")
        return StreamEvent.OKAY, {}
    {% elif cookiecutter.data_type == 'video' -%}
    def process_frame(self, stream, data_files: List[DataFile]) -> Tuple[StreamEvent, Union[Dict, str]]:
        for df in data_files:
            self.logger.info(f"DataFile.content: {df.content.shape}")
        return StreamEvent.OKAY, {}
    {% elif cookiecutter.data_type == 'image' -%}
    def process_frame(self, stream, data_files: List[DataFile]) -> Tuple[StreamEvent, Union[Dict, str]]:
        for df in data_files:
            self.logger.info(f"DataFile.content: {df.content.shape}")
        return StreamEvent.OKAY, {}
    {%- endif -%}



