import logging
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
import onnxruntime as ort
from pydantic import HttpUrl

from highlighter.client.io import download_bytes, get_cache_path

HL_GPU_DEVICE_ID = os.environ.get("HL_GPU_DEVICE_ID", 0)
HL_MODEL_HEAD_INDEX = os.environ.get("HL_MODEL_HEAD_INDEX", 0)
LOGGER = logging.getLogger("OnnxPredictor")
ort.set_default_logger_severity(os.environ.get("ONNX_RUNTIME_LOGLEVEL", 3))


def is_cuda_available():
    providers = ort.get_available_providers()
    return "CUDAExecutionProvider" in providers


def is_url(s):
    try:
        url = HttpUrl(s).unicode_string()  # pyright: ignore
        return url
    except Exception:
        return False


class OnnxPredictor:
    """Loads an onnx model and does prediction

    Set log level:
       set the ONNX_RUNTIME_LOGLEVEL environment variable

    Set gpu id
       set the HL_GPU_DEVICE_ID environment variable

    Select a different head when reading TrainingRunInterface.model_outputs
       set the HL_MODEL_HEAD_INDEX environment variable
    """

    def __init__(
        self,
        onnx_file: Union[str, Path],
        device_id=HL_GPU_DEVICE_ID,
        ort_custom_op_path: Optional[str] = None,
    ):
        session_options = ort.SessionOptions()
        # register custom op for onnxruntime
        if ort_custom_op_path not in (None, ""):
            session_options.register_custom_ops_library(str(ort_custom_op_path))

        providers = ["CPUExecutionProvider"]
        provider_options = [{}]
        self.is_cuda_available = is_cuda_available()
        if self.is_cuda_available:
            providers.insert(0, "CUDAExecutionProvider")
            provider_options.insert(0, {"device_id": device_id})
        LOGGER.debug(f"is_cuda_available={self.is_cuda_available}")
        LOGGER.debug(f"provider_options={provider_options}")

        if url := is_url(onnx_file):
            onnx_file = get_cache_path(url)
            download_bytes(url, save_path=onnx_file, check_cached=True)

        self.sess = ort.InferenceSession(
            str(onnx_file),
            sess_options=session_options,
            providers=providers,
            provider_options=provider_options,
        )

        self.io_binding = self.sess.io_binding()

        _inputs = self.sess.get_inputs()
        if len(_inputs) > 1:
            raise ValueError(f"Expected only 1 input name for onnx-runtime session, got: {_inputs}")
        self.input_name = _inputs[0].name
        input_shape = _inputs[0].shape

        # 3D input probably indicates an ONNX model that expects a single image
        if len(input_shape) == 3:
            raise ValueError(
                f"Onnx models must have batch dimension. This Onnx model has an input of shape {input_shape}"
            )
        self.batch_size = input_shape[0]
        if isinstance(self.batch_size, int) and self.batch_size != 1:
            raise ValueError(
                f"Batch size must be the integer 1 or a symbolic value to indicate dynamic match size, got: {type(self.batch_size).__name__}: {self.batch_size}"
            )

        self.output_names = [_.name for _ in self.sess.get_outputs()]
        LOGGER.debug(f"onnxruntime session instantiated, input_shape {input_shape}")

    def predict(self, input_batch):
        if self.batch_size == 1:
            outputs = []
            for single_input in input_batch:
                single_input = np.expand_dims(single_input, axis=0)
                outputs.append(self.predict_batch(single_input)[0])

        elif not isinstance(self.batch_size, int):  # Symbolic value indicates dynamic batch size
            outputs = self.predict_batch(input_batch)
        else:
            raise ValueError(f"Unhandled batch size: {self.batch_size}")
        return outputs

    def predict_batch(self, input_batch):
        self.io_binding.bind_cpu_input(  # No-op if gpu is not available
            self.input_name,
            input_batch,
        )

        for name in self.output_names:
            self.io_binding.bind_output(name)

        # run session to get outputs
        self.sess.run_with_iobinding(self.io_binding)
        ort_outputs = self.io_binding.copy_outputs_to_cpu()  # No copy is performed if gpu is not available
        return ort_outputs
