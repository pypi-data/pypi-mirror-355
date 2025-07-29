import io
from pathlib import Path
from typing import List, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

from highlighter.agent.capabilities.image_to_scalar import NeuFlowV2
from highlighter.client.io import download_bytes

DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "neuflow_sintel.onnx"
DEFAULT_MODEL_URL = (
    "https://github.com/ibaiGorordo/ONNX-NeuFlowV2-Optical-Flow/releases/download/0.1.0/neuflow_sintel.onnx"
)


class OpticalFlow:
    """
    A standalone optical flow class that calculates a movement score
    based on optical flow between consecutive frames.
    """

    def __init__(
        self,
        model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
        use_gpu: bool = True,
        blur_kernel: tuple = (3, 3),
    ) -> None:
        """
        Initialize the OpticalFlow class.

        Args:
            model_path (str): Path to the optical flow model file.
            use_gpu (bool): Whether to use GPU for preprocessing.
            blur_kernel (tuple): Size of Gaussian blur kernel for preprocessing.
        Returns:
            None
        """
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
        self.blur_kernel = blur_kernel
        self.estimator = self._load_model()  # load the model from the model_path
        self.prev_frame = None

        # Image preprocessing transform pipeline
        self.preprocess_frame = T.Compose(
            [
                T.ToTensor(),  # Convert image to tensor
                T.ConvertImageDtype(torch.float32),  # Convert image to float32
                T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),  # Normalize image
            ]
        )

        print(f"Initialized OpticalFlow on device: {self.device}")

    def _load_model(self) -> NeuFlowV2:
        """
        Load the NeuFlowV2 optical flow model.

        Returns:
            The loaded NeuFlowV2 model instance.
        """
        self.model_path = Path(self.model_path)
        default_path = Path(DEFAULT_MODEL_PATH)

        # Check if file exists and compare names safely
        if not self.model_path.exists():
            # Create directory
            self.model_path.parent.mkdir(parents=True, exist_ok=True)

            # Safe comparison using Path objects
            if self.model_path.name == default_path.name:
                print(f"Downloading model from {DEFAULT_MODEL_URL}...")
                download_bytes(DEFAULT_MODEL_URL, save_path=self.model_path)
                print(f"Downloaded to: {self.model_path}")
            else:
                raise FileNotFoundError(f"Model not found: {self.model_path}")

        return NeuFlowV2(self.model_path)

    def update(self, image) -> float:
        """
        Update the algorithm with a new image and return the latest movement score.

        The movement score is calculated as the sum of the magnitudes of all optical
        flow vectors between the current image and the previous image.

        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV).

        Returns:
            float: Movement score indicating the amount of motion between frames.
        """
        # Apply Gaussian blur to reduce noise
        filtered_frame = cv2.GaussianBlur(image, self.blur_kernel, 0)

        # frame_tensor is CHW
        frame_tensor = self.preprocess_frame(filtered_frame).to(self.device)

        # If this is the first frame, store it and return 0
        if self.prev_frame is None:
            self.prev_frame = frame_tensor
            return 0.0  # Return 0 if it's the first frame

        # Convert tensors back to numpy for OpticalFlow estimation
        # convert from CHW back to HWC
        prev_frame_np = (self.prev_frame.cpu().permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)

        curr_frame_np = (frame_tensor.cpu().permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)

        # Calculate optical flow
        flow_vectors = self.estimator(prev_frame_np, curr_frame_np)

        # Store current frame for next comparison
        self.prev_frame = frame_tensor

        return flow_vectors

    def compute_movement_scores(self, flow_vectors: np.ndarray) -> Tuple[float, float, float]:
        """Computes the movement score from the flow vectors"""
        u, v = flow_vectors[..., 0], flow_vectors[..., 1]
        magnitude = np.sqrt(u**2 + v**2)
        movement_sum = np.sum(magnitude)
        movement_mean = np.mean(magnitude)
        movement_median = np.median(magnitude)

        return movement_sum, movement_mean, movement_median

    def reset(self):
        """
        Reset the optical flow state.
        """
        self.prev_frame = None

    @staticmethod
    def draw_flow(curr_frame, flow, step=20) -> np.ndarray:
        # Create a copy of the frame for overlay
        frame_with_flow = curr_frame.copy()

        # Sample flow vectors on a grid
        h, w = flow.shape[:2]
        y, x = np.mgrid[step // 2 : h : step, step // 2 : w : step].reshape(2, -1).astype(int)
        fx, fy = flow[y, x].T

        # Create lines for visualization (start and end points)
        lines = np.vstack([x, y, x + fx, y + fy]).T.reshape(-1, 2, 2)
        lines = lines.astype(np.int32)

        # Compute magnitude and angle for color coding
        mag, ang = cv2.cartToPolar(fx, fy)
        mag = np.clip(mag, 0, 20)  # Cap magnitude for visualization
        ang = ang * 180 / np.pi  # Convert to degrees

        # Draw flow vectors as colored lines
        for (x1, y1), (x2, y2), m, a in zip(lines[:, 0], lines[:, 1], mag, ang):
            # Color based on angle (hue) and magnitude (brightness)
            hsv = np.zeros((1, 1, 3), dtype=np.uint8)
            hsv[0, 0, 0] = (a / 2)[0]  # Hue from angle
            hsv[0, 0, 1] = 255  # Full saturation
            hsv[0, 0, 2] = int((255 * m / 20)[0])  # Value from magnitude
            color = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
            cv2.line(frame_with_flow, (x1, y1), (x2, y2), color.tolist(), 4)
            cv2.circle(frame_with_flow, (x2, y2), 1, color.tolist(), -1)

        return frame_with_flow

    @staticmethod
    def overlay_movement_score_fig(
        frame_indices: List[int],
        movement_sums: List[float] = None,
        movement_means: List[float] = None,
        movement_medians: List[float] = None,
        current_frame_idx: int = 0,
        display_type: str = "median",  # "sum", "mean", "median", or "all" #if you want to overlay all of them with video, change this to all (will have option in CLI to help change this one, read CLI)
        width: int = 600,
        height: int = 550,
    ) -> tuple:

        plt.style.use("dark_background")

        if display_type == "all":
            # Create 3 subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(width / 100, height / 100), dpi=100)
            axes = [ax1, ax2, ax3]

            plot_configs = [
                (movement_sums, "Sum", "#00BFFF", ax1),
                (movement_means, "Mean", "#00FF7F", ax2),
                (movement_medians, "Median", "#FFD700", ax3),
            ]

            for scores, title, color, ax in plot_configs:
                if scores and len(scores) > 1:
                    ax.plot(frame_indices[: len(scores)], scores, color=color, linewidth=2, alpha=0.9)
                    if current_frame_idx < len(scores):
                        ax.plot(current_frame_idx, scores[current_frame_idx], "ro", markersize=6)
                    ax.fill_between(frame_indices[: len(scores)], scores, alpha=0.3, color=color)

                ax.set_title(f"Movement Score ({title})", fontsize=8, color="white", fontweight="bold")
                ax.set_ylabel(title, fontsize=7, color="white")
                ax.grid(True, alpha=0.4, color="gray", linestyle="-", linewidth=0.8)
                ax.set_facecolor("black")
                ax.tick_params(colors="white", labelsize=6)

            axes[-1].set_xlabel("Frame", fontsize=7, color="white")

        else:
            # Create single plot
            fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)

            # Select data and styling based on display_type
            if display_type == "sum" and movement_sums:
                scores, title, color = movement_sums, "Sum", "#00BFFF"
            elif display_type == "mean" and movement_means:
                scores, title, color = movement_means, "Mean", "#00FF7F"
            elif display_type == "median" and movement_medians:
                scores, title, color = movement_medians, "Median", "#FFD700"
            else:
                # Default to median or first available
                if movement_medians:
                    scores, title, color = movement_medians, "Median", "#FFD700"
                elif movement_means:
                    scores, title, color = movement_means, "Mean", "#00FF7F"
                elif movement_sums:
                    scores, title, color = movement_sums, "Sum", "#00BFFF"
                else:
                    scores, title, color = [], "No Data", "#FFFFFF"

            if scores and len(scores) > 1:
                ax.plot(frame_indices[: len(scores)], scores, color=color, linewidth=2.5, alpha=0.9)
                if current_frame_idx < len(scores):
                    ax.plot(
                        current_frame_idx,
                        scores[current_frame_idx],
                        "ro",
                        markersize=8,
                        markerfacecolor="red",
                        markeredgecolor="white",
                        markeredgewidth=1,
                    )
                ax.fill_between(frame_indices[: len(scores)], scores, alpha=0.3, color=color)

            ax.set_title(f"Movement Score ({title})", fontsize=10, color="white", fontweight="bold", pad=10)
            ax.set_xlabel("Frame", fontsize=8, color="white")
            ax.set_ylabel("Score", fontsize=8, color="white")
            ax.grid(True, alpha=0.4, color="gray", linestyle="-", linewidth=0.8)
            ax.set_facecolor("black")
            ax.tick_params(colors="white", labelsize=7)

        fig.patch.set_facecolor("black")
        fig.patch.set_alpha(0.9)
        plt.tight_layout()

        # Convert to image
        buf = io.BytesIO()
        fig.savefig(
            buf, format="png", facecolor="black", edgecolor="none", bbox_inches="tight", pad_inches=0.05
        )
        buf.seek(0)

        plot_img = np.array(Image.open(buf))
        plt.close(fig)

        if plot_img.shape[2] == 4:
            alpha = plot_img[:, :, 3] / 255.0
            plot_bgr = cv2.cvtColor(plot_img[:, :, :3], cv2.COLOR_RGB2BGR)
            return plot_bgr, alpha
        else:
            plot_bgr = cv2.cvtColor(plot_img, cv2.COLOR_RGB2BGR)
            alpha = np.ones(plot_img.shape[:2])
            return plot_bgr, alpha

    @staticmethod
    def plot_movement_score(
        frame: np.ndarray,
        plot_img: np.ndarray,
        alpha: np.ndarray,
        position: str = "bottom-right",
        margin: int = 30,
    ) -> np.ndarray:

        frame_h, frame_w = frame.shape[:2]
        plot_h, plot_w = plot_img.shape[:2]

        # Calculate position for bottom-right
        if position == "bottom-right":
            start_y = frame_h - plot_h - margin
            start_x = frame_w - plot_w - margin
        elif position == "bottom-left":
            start_y = frame_h - plot_h - margin
            start_x = margin
        elif position == "top-right":
            start_y = margin
            start_x = frame_w - plot_w - margin
        elif position == "top-left":
            start_y = margin
            start_x = margin
        else:
            # Default to bottom-right
            start_y = frame_h - plot_h - margin
            start_x = frame_w - plot_w - margin

        # Ensure don't go out of bounds
        start_y = max(0, min(start_y, frame_h - plot_h))
        start_x = max(0, min(start_x, frame_w - plot_w))

        # Validate bounds
        if start_y + plot_h > frame_h or start_x + plot_w > frame_w:
            print(f"ERROR: Plot no fit! Plot end: ({start_x + plot_w}, {start_y + plot_h})")
            return frame

        # Get region of interest
        roi = frame[start_y : start_y + plot_h, start_x : start_x + plot_w].copy()

        # Blend images using alpha channel
        for c in range(3):
            roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * plot_img[:, :, c]

        # Update frame
        frame[start_y : start_y + plot_h, start_x : start_x + plot_w] = roi

        return frame


# Add CLI stuff
import json
from pathlib import Path

import click
import cv2

from highlighter.agent.capabilities.sources import VideoFrameIterator

DEFAULT_MODEL_PATH = Path("models/neuflow_sintel.onnx")


class _VideoBuilder:
    """Build output video with optical flow visualization"""

    def __init__(self, output_video_path, width, height, fps):
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    def update(self, frame):
        # Write frame to output video
        self.out.write(frame)

    def release(self):
        self.out.release()


@click.group()
def flow_group():
    pass


@flow_group.command("compute")
@click.argument("video_path", type=str)
@click.option("--model-path", type=str, required=False, default=DEFAULT_MODEL_PATH)
@click.option("--fps", type=int, required=False, default=0)
@click.option("--max-frames", type=int, required=False, default=0)
@click.option(
    "--draw-scores", is_flag=True, help="Overlay movement score graph on video (create video with plot)"
)
@click.option("--draw-flow", is_flag=True, help="Draw colored optical flow vectors on video frame")
@click.option("--draw-plot", is_flag=True, help="Generate image with movement score plot :sum, mean, median")
@click.option(
    "--score-type",
    type=click.Choice(["sum", "mean", "median", "all"]),  # all will plot all of them of vid
    default="median",
    help="Type of movement score to plot",
)
def compute(video_path, model_path, max_frames, fps, draw_scores, draw_flow, draw_plot, score_type):

    if not max_frames:
        max_frames = float("inf")

    of = OpticalFlow(model_path=model_path)
    video_frames = VideoFrameIterator(source_urls=[video_path])

    prev_frame = next(video_frames).content
    if prev_frame.shape[2] == 3:
        prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2BGR)

    of.update(prev_frame)

    if draw_flow or draw_scores:
        output_video_path = f"{Path(video_path).stem}_optical_flow.mp4"
        frame_count = int(video_frames._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video_frames._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video_frames._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = video_frames._cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(video_frames._cap.get(cv2.CAP_PROP_FRAME_COUNT))

        vb = _VideoBuilder(output_video_path, width, height, fps)
        print(f"Creating output video: {output_video_path}")
        print(f"Video properties: {width}x{height} @ {fps}fps, {total_frames} frames")

    frame_number = 0
    _sums = []
    _means = []
    _medians = []
    _frame_indices = []

    while True:
        try:
            cur_frame = next(video_frames).content
            if cur_frame.shape[2] == 3:
                cur_frame = cv2.cvtColor(cur_frame, cv2.COLOR_RGB2BGR)
            elif cur_frame.shape[2] == 4:
                cur_frame = cv2.cvtColor(cur_frame, cv2.COLOR_RGBA2BGR)
        except StopIteration:
            print(f"End of video, processed {frame_number} frames")
            break

        flow = of.update(cur_frame)
        f_sum, f_mean, f_median = of.compute_movement_scores(flow)
        _sums.append(int(f_sum))
        _means.append(float(f_mean))
        _medians.append(float(f_median))
        _frame_indices.append(frame_number)

        if not (frame_number % 50):  # Print every 50 frames
            print(f"Frame {frame_number}: Sum:{int(f_sum)}, Mean:{f_mean:0.2f}, Med:{f_median:0.2f}")

        if draw_flow or draw_scores:
            output_frame = cur_frame.copy()

            if draw_flow:
                output_frame = of.draw_flow(output_frame, flow)

            if draw_scores:
                # Select which scores to plot
                if score_type == "sum":
                    display_type = "sum"
                    plot_title = "Movement Score (Sum)"
                elif score_type == "mean":
                    display_type = "mean"
                    plot_title = "Movement Score (Mean)"
                elif score_type == "median":
                    display_type = "median"
                    plot_title = "Movement Score (Median)"
                else:
                    display_type = "all"
                    plot_title = "Movement Score (All)"

                plot_img, alpha = of.overlay_movement_score_fig(
                    _frame_indices,
                    movement_sums=_sums,
                    movement_means=_means,
                    movement_medians=_medians,
                    current_frame_idx=frame_number,
                    display_type=display_type,
                )
                # plot at bottom-right corner
                output_frame = of.plot_movement_score(
                    output_frame, plot_img, alpha, position="bottom-right", margin=30
                )

            vb.update(output_frame)

        prev_frame = cur_frame
        frame_number += 1

        if frame_number >= max_frames:
            print(f"Exiting at max_frames: {max_frames}")
            break

    # Save movement scores to JSON
    with open(f"{Path(video_path).stem}_flow_scores.json", "w") as f:
        json.dump(
            {"sums": _sums, "means": _means, "medians": _medians, "frame_indices": _frame_indices},
            f,
            indent=2,
        )

    if draw_plot:
        plot_img, alpha = of.overlay_movement_score_fig(
            _frame_indices,
            movement_sums=_sums,
            movement_means=_means,
            movement_medians=_medians,
            current_frame_idx=len(_medians) - 1 if _medians else 0,
            display_type="all",
            width=1200,
            height=900,
        )

    fig_save_path = f"{Path(video_path).stem}_movement_scores.png"
    cv2.imwrite(fig_save_path, plot_img)
    print(f"Saved combined plot: {fig_save_path}")

    if draw_flow or draw_scores:
        vb.release()
        print(f"Video processing complete: {output_video_path}")


if __name__ == "__main__":
    flow_group()
