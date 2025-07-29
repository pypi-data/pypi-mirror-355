# Usage
# ~~~~~
# cd pavilion_farms_monitor  # repository top-level
# aiko_pipeline create agents/assessment_pipeline.json -s 1  # -ll debug
#
# To Do
# ~~~~~
# - Configure nix environment to include HL SDK
#   - Update this source code to use HL SDK instead of the mock methods below
#
# - Fix random Pipeline hangs when using ImageGather StreamEvent.DROP_FRAME :(
#   - Currently, using a solid work-around instead of StreamEvent.DROP_FRAME
#
# - Implement ImageToVideo parameter to decide whether the resulting video
#   is provided in-memory or as a file in the file-system
#
# - Decide whether to keep the ImageToVideo OpenCV implementation as an option ?

import io
import os
import threading
from datetime import datetime
from typing import Optional, Tuple

import aiko_services as aiko
import av

from highlighter.agent.capabilities import Capability
from highlighter.agent.capabilities.base_capability import StreamEvent
from highlighter.client import HLClient, assessments, data_files

__all__ = ["ImageGather"]

_GATHER_SIZE = 25 * 10  # frames * seconds


class ImageGather(Capability):
    class DefaultStreamParameters(Capability.DefaultStreamParameters):
        task_id: str
        data_source_id: int

        list_size: int = _GATHER_SIZE
        frame_rate: int = 25
        bit_rate: int = 1000000
        template: str = "video_{:05d}.mp4"
        resolution: Optional[str] = None

    def __init__(self, context: aiko.ContextPipelineElement):
        context.set_protocol("image_gather:0")
        context.get_implementation("PipelineElement").__init__(self, context)
        self._threads = []
        client = HLClient.get_client()
        self._client_endpoint = client.endpoint_url
        self._client_token = client.api_token

    def _get_new_client(self) -> HLClient:
        return HLClient.from_credential(self._client_token, self._client_endpoint)

    def start_stream(self, stream, stream_id):
        self.start_time = datetime.now()
        self.chunk_start_time = self.start_time
        stream.variables["image_gather_list"] = []
        return aiko.StreamEvent.OKAY, {}

    def process_frame(self, stream, data_files) -> Tuple[StreamEvent, dict]:
        images = [(d.content, d.recorded_at) for d in data_files]
        list_size, _ = self.get_parameter("list_size")
        image_gather_list = stream.variables["image_gather_list"]
        if image_gather_list == []:
            prev = self.chunk_start_time
            self.chunk_start_time = images[0][1]
            print("first frame", self.chunk_start_time, self.chunk_start_time - prev)
        image_gather_list += images

        if len(image_gather_list) < list_size:
            return aiko.StreamEvent.OKAY, {"images": [], "start_time": None}  # TODO: Workaround :(

        stream.variables["image_gather_list"] = []
        self.logger.debug(f"{self.my_id()}: images gathered")
        self._start_upload(stream, image_gather_list)

        return aiko.StreamEvent.OKAY, {}

    def stop_stream(self, stream, stream_id):
        image_gather_list = stream.variables["image_gather_list"]

        if len(image_gather_list):
            self._start_upload(stream, image_gather_list)

        self.logger.debug(f"{self.my_id()}: waiting for {len(self._threads)} upload threads to complete")
        for t in self._threads:
            t.join()

        self._assessment_finalise(stream.variables)

        return StreamEvent.OKAY, {}

    def _start_upload(self, stream, image_gather_list):
        template, _ = self.get_parameter("filename_template")
        path = template.format(int(image_gather_list[0][1].timestamp()))
        thread = threading.Thread(
            target=self._images_to_video, args=(image_gather_list, path, stream.variables)
        )
        thread.start()
        self._threads.append(thread)

    def _images_to_video(self, images, path, cache):
        bit_rate, _ = self.get_parameter("bit_rate")
        frame_rate, _ = self.get_parameter("frame_rate")
        first_image = images[0][0]
        resolution_default = f"{first_image.shape[1]}x{first_image.shape[0]}"
        resolution, _ = self.get_parameter("resolution")
        if resolution is None:
            resolution = resolution_default
        width, height = resolution.split("x")

        buffer = io.BytesIO()
        container = av.open(buffer, mode="w", format="mp4")
        video_stream = container.add_stream("h264", rate=frame_rate)
        video_stream.bit_rate = bit_rate if bit_rate else video_stream.bit_rate
        video_stream.pix_fmt = "yuv420p"
        video_stream.width, video_stream.height = int(width), int(height)

        for timestamp, image in enumerate(images):
            #   video_frame = av.VideoFrame.from_image(pil_image)  # PIL Image
            video_frame = av.VideoFrame.from_ndarray(image[0])  # Numpy Image
            video_frame.pts = timestamp
            packet = video_stream.encode(video_frame)
            if packet is not None:
                container.mux(packet)

        final_packet = video_stream.encode(None)
        if final_packet is not None:
            container.mux(final_packet)
        container.close()

        video_mp4 = buffer.getvalue()
        try:
            with open(path, "wb") as file:
                file.write(video_mp4)
            self._assessment_append_paths(path, cache, images[0][1])
        finally:
            if os.path.exists(path):
                os.remove(path)
            else:
                self.logger.warning(f'{self.my_id()}: Assessment file: "{path}" not found')
        return path

    def _assessment_append(self, path, cache, start_time):
        data_source_id, found = self.get_parameter("data_source_id")
        if not found:
            raise KeyError('Must provide "data_source_id" parameter')

        task_id, found = self.get_parameter("task_id")
        if not found:
            raise KeyError('Must provide "task_id" parameter')

        hl_client = self._get_new_client()
        if "assessment" not in cache:

            data_file = data_files.create_data_file(
                hl_client, path, data_source_id, recorded_at=start_time.isoformat()
            )

            assessment = assessments.create_assessment_not_finalised(
                hl_client, task_id=str(task_id), image_id=data_file.id
            )
            cache["assessment"] = assessment
            assessments.append_data_files_to_not_finalised_assessment(
                hl_client, cache["assessment"], [data_file]
            )

        else:

            data_file = data_files.create_data_file(
                hl_client, path, data_source_id, recorded_at=start_time.isoformat()
            )

            assessments.append_data_files_to_not_finalised_assessment(
                hl_client, cache["assessment"], [data_file]
            )

    def _assessment_append_paths(self, path, cache, start_time):
        self.logger.info(f"{path} {start_time}")
        self._assessment_append(path, cache, start_time)

    def _assessment_finalise(self, cache):
        if "assessment" in cache:
            hl_client = self._get_new_client()
            assessments.finalise(hl_client, cache["assessment"])
            del cache["assessment"]
