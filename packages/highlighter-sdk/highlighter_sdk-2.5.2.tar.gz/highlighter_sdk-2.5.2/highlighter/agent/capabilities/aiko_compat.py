# To Do
# ~~~~~
# - PackDataFiles / UnpackDataFiles applies to any third-party "raw data"
#   and is not specific to Aiko Services compatibility
#   - Move the "pack" and "unpack" functions into "client/data_files.py"
#   - This file can then adapt those two functions into Capabilities
#   - Rename this file to something that represents a more general purpose

from datetime import datetime
from typing import Dict, List, Tuple
from uuid import uuid4

from highlighter.agent.capabilities.base_capability import Capability, StreamEvent
from highlighter.client.base_models import DataFile

__all__ = ["PackDataFiles", "UnpackDataFiles"]


class PackDataFiles(Capability):

    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        input_key: str
        content_type: str
        output_key: str = "data_files"
        output_empty_entities: bool = False

    @property
    def input_key(self):
        return self._get_parameter("input_key")[0]

    @property
    def content_type(self):
        return self._get_parameter("content_type")[0]

    @property
    def output_key(self):
        return self._get_parameter("output_key")[0]

    @property
    def output_empty_entities(self):
        return self._get_parameter("output_empty_entities")[0]

    def process_frame(self, stream, *args, **kwargs) -> Tuple[StreamEvent, Dict]:
        data_files = []
        inputs = kwargs[self.input_key]
        for input in inputs:
            file_id = uuid4()
            data_file = DataFile(
                content=input, content_type=self.content_type, file_id=file_id, recorded_at=datetime.now()
            )
            #################################################################
            # DataFile "identity_map" is a class (static) variable,         #
            # which holds onto the "content" reference, which may be huge.  #
            # For example, RTSP camera with up-to 3840 x 2160 x 3 channels. #
            # So, 24 Mb images at 25 FPS is a 600 Mb per second memory leak #
            #################################################################
            data_file._get_identity_map().remove(DataFile, file_id)
            data_files.append(data_file)

        if "timestamps" in stream.variables:
            timestamps = [datetime.fromtimestamp(ts) for ts in stream.variables["timestamps"]]
        else:
            rate, found = self.pipeline.pipeline_graph.nodes()[0].element.get_parameter("rate")
            if not found:
                raise ValueError("Cannot determine frame 'rate' from head node")

            frame_counter = getattr(self, "frame_counter", 0)
            timestamps = [1 / rate * (i + frame_counter) for i in range(len(inputs))]
            self.frame_counter = frame_counter + len(timestamps)

            # ToDo: Update the aiko fork when aiko starts putting `timestamps` in stream.variables
            #       the above code can be removed and we simply raise
            # raise ValueError("stream.variables must have 'timestamps' in order to create a DataFile object")

        data_files = [
            DataFile(recorded_at=ts, content=i, content_type=self.content_type, file_id=uuid4())
            for i, ts in zip(inputs, timestamps)
        ]
        result = {self.output_key: data_files}
        if self.output_empty_entities:
            result["entities"] = [{}] * len(data_files)

        return StreamEvent.OKAY, result


class UnpackDataFiles(Capability):

    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        output_key: str

    @property
    def output_key(self):
        return self._get_parameter("output_key")[0]

    def process_frame(self, stream, data_files: List[DataFile], *args, **kwargs) -> Tuple[StreamEvent, Dict]:
        output = [d.content for d in data_files]
        return StreamEvent.OKAY, {self.output_key: output}
