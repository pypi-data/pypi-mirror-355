from typing import Dict, List, Optional, Tuple
from uuid import UUID

from highlighter.agent.capabilities.base_capability import Capability, StreamEvent
from highlighter.client.base_models.data_file import DataFile
from highlighter.predictors.onnx_yolov8 import OnnxYoloV8 as Predictor

__all__ = ["OnnxYoloV8"]


class OnnxYoloV8(Capability):

    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        onnx_file: str
        num_classes: int = 80
        class_lookup: Optional[Dict[int, Tuple[UUID, str]]] = None
        conf_thresh: float = 0.1
        nms_iou_thresh: float = 0.5
        is_absolute: bool = True

    def __init__(self, context, *args, **kwargs):
        context.get_implementation("PipelineElement").__init__(self, context, *args, **kwargs)
        self._predictor: Optional[Predictor] = None
        self._init_params: Optional[Tuple] = tuple()

    def start_stream(self, stream, stream_id, use_create_frame=True):
        super().start_stream(stream, stream_id, use_create_frame=use_create_frame)
        onnx_file, found = self._get_parameter("onnx_file")
        assert found

        num_classes, found = self._get_parameter("num_classes")
        assert found

        class_lookup, _ = self._get_parameter("class_lookup", default=None)
        conf_thresh, _ = self._get_parameter("conf_thresh")
        nms_iou_thresh, _ = self._get_parameter("nms_iou_thresh")
        is_absolute, _ = self._get_parameter("is_absolute")

        new_init_params = (onnx_file, num_classes, class_lookup, conf_thresh, nms_iou_thresh, is_absolute)

        if (self._predictor is None) or (new_init_params != self._init_params):
            self._predictor = Predictor(
                onnx_file,
                num_classes,
                class_lookup=class_lookup,
                conf_thresh=conf_thresh,
                nms_iou_thresh=nms_iou_thresh,
                is_absolute=is_absolute,
            )

        return StreamEvent.OKAY, {}

    def process_frame(self, stream, data_files: List[DataFile]) -> Tuple[StreamEvent, Dict]:
        annotations = self._predictor.predict(data_files)
        self.logger.debug(f"annotations: {annotations}")
        return StreamEvent.OKAY, {"annotations": annotations}
