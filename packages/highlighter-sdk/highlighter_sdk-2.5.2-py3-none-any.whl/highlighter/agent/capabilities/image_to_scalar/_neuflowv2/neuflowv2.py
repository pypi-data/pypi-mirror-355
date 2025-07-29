# Add neuflow stuff
import os
import time

import cv2
import numpy as np
import onnxruntime
import requests
import tqdm

available_models = ["neuflow_mixed", "neuflow_sintel", "neuflow_things"]


def download_model(url: str, path: str):
    print(f"Downloading model from {url} to {path}")
    r = requests.get(url, stream=True, timeout=30)
    with open(path, "wb") as f:
        total_length = int(r.headers.get("content-length"))
        for chunk in tqdm.tqdm(
            r.iter_content(chunk_size=1024 * 1024),
            total=total_length // (1024 * 1024),
            bar_format="{l_bar}{bar:10}",
        ):
            if chunk:
                f.write(chunk)
                f.flush()


def check_model(model_path: str):
    if os.path.exists(model_path):
        return

    model_name = os.path.basename(model_path).split(".")[0]
    if model_name not in available_models:
        raise ValueError(f"Invalid model name: {model_name}")
    url = f"https://github.com/ibaiGorordo/ONNX-NeuFlowV2-Optical-Flow/releases/download/0.1.0/{model_name}.onnx"
    download_model(url, model_path)


class NeuFlowV2:

    def __init__(self, path: str):
        check_model(path)

        # Initialize model
        self.session = onnxruntime.InferenceSession(path, providers=onnxruntime.get_available_providers())

        # Get model info
        self.get_input_details()
        self.get_output_details()

    def __call__(self, img_prev: np.ndarray, img_now: np.ndarray) -> np.ndarray:
        return self.estimate_flow(img_prev, img_now)

    def estimate_flow(self, img_prev: np.ndarray, img_now: np.ndarray) -> np.ndarray:
        input_tensors = self.prepare_inputs(img_prev, img_now)

        # Perform inference on the image
        outputs = self.inference(input_tensors)

        return self.process_output(outputs[0])

    def prepare_inputs(self, img_prev: np.ndarray, img_now: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        self.img_height, self.img_width = img_now.shape[:2]

        input_prev = self.prepare_input(img_prev)
        input_now = self.prepare_input(img_now)

        return input_prev, input_now

    def prepare_input(self, img: np.ndarray) -> np.ndarray:
        # Resize input image
        input_img = cv2.resize(img, (self.input_width, self.input_height))

        # Scale input pixel values to 0 to 1
        input_img = input_img / 255.0
        input_img = input_img.transpose(2, 0, 1)
        input_tensor = input_img[np.newaxis, :, :, :].astype(np.float32)
        return input_tensor

    def inference(self, input_tensors: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        start = time.perf_counter()
        outputs = self.session.run(
            self.output_names, {self.input_names[0]: input_tensors[0], self.input_names[1]: input_tensors[1]}
        )

        print(f"Inference time: {(time.perf_counter() - start) * 1000:.2f} ms")
        return outputs

    def process_output(self, output) -> np.ndarray:
        flow = output.squeeze().transpose(1, 2, 0)

        return cv2.resize(flow, (self.img_width, self.img_height))

    def get_input_details(self):
        model_inputs = self.session.get_inputs()
        self.input_names = [model_inputs[i].name for i in range(len(model_inputs))]

        input_shape = model_inputs[0].shape
        self.input_height = input_shape[2]
        self.input_width = input_shape[3]

    def get_output_details(self):
        model_outputs = self.session.get_outputs()
        self.output_names = [model_outputs[i].name for i in range(len(model_outputs))]
