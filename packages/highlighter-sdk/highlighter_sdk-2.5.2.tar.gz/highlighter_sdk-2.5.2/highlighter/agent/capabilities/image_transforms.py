from typing import Dict, List, Optional, Tuple

from aiko_services.elements.media import image_io

from highlighter.agent.capabilities import Capability
from highlighter.agent.capabilities.base_capability import StreamEvent
from highlighter.client.base_models.data_file import DataFile

__all__ = ["ImageOverlay", "ImageResize"]


class ImageResize(Capability):
    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        width: int = 0  # If zero, will maintain aspect ratio with respect to height
        height: int = 0  # If zero, will maintain aspect ratio with respect to width

    @property
    def width(self) -> int:
        return self._get_parameter("width")[0]

    @property
    def height(self) -> int:
        return self._get_parameter("height")[0]

    def process_frame(self, data_files: List[DataFile]) -> Tuple[StreamEvent, Optional[Dict]]:
        data_files = [df.resize(width=self.width, height=self.height) for df in data_files]
        return StreamEvent.OKAY, {"data_files": data_files}


class ImageOverlay(image_io.ImageOverlay, Capability):

    def process_frame(self, stream, data_files, annotations):
        for df, annos in zip(data_files, annotations):
            df_anns = [a for a in annos if a.data_file_id == df.file_id]
            overlay = df.draw_annotations(df_anns)
            df.content = overlay
        return StreamEvent.OKAY, {"data_files": data_files}
