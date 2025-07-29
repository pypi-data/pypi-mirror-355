import shutil
from copy import deepcopy
from pathlib import Path
from typing import Optional

import ultralytics
import yaml

from highlighter.datasets.cropping import CropArgs
from highlighter.trainers._scaffold import TrainerType

__all__ = ["generate", "prepare_datasets", "train", "export"]


def generate(training_run_dir: Path, trainer: TrainerType):
    shutil.copy(Path(__file__).parent / "template.py", training_run_dir / "trainer.py")

    overrides_lookup = {
        TrainerType.YOLO_DET: {
            "model": "yolov8m.pt",
            "task": "detect",
        },
        TrainerType.YOLO_SEG: {
            "model": "yolov8m-seg.pt",
            # Ensures overlapping masks are merged, which is critical for accurate
            # segmentation in datasets with overlapping objects (default is True, but
            # explicitly set for clarity).
            "overlap_mask": True,
            # Controls mask resolution; 4 is the default and balances detail
            # with computational efficiency, suitable for most segmentation tasks.
            "mask_ratio": 4,
            "task": "segment",
        },
        TrainerType.YOLO_CLS: {
            "model": "yolov8m-cls.pt",
            # Adds regularization to prevent overfitting, which is more common
            # in classification tasks with large datasets; 0.1 is a modest starting point.
            "dropout": 0.1,
            # Classification often works with smaller images than detection/segmentation;
            # 224 is a common size (e.g., ImageNet), balancing detail and speed.
            "imgsz": 224,
            "task": "classify",
        },
    }

    overrides = overrides_lookup[trainer]

    default_cfg = dict(ultralytics.cfg.get_cfg())
    default_cfg.update(overrides)
    default_cfg["project"] = "runs"
    default_cfg["opset"] = 14
    default_cfg["format"] = "onnx"
    default_cfg["dynamic"] = False
    with (training_run_dir / "cfg.yaml").open("w") as f:
        yaml.dump(default_cfg, f)


def prepare_datasets(datasets):
    # When creating a training run in Highlighter the train split is required
    # but a user can supply either a test or dev set, or both. If not both we
    # duplicate the one that exists here
    if "test" not in datasets:
        datasets["test"] = deepcopy(datasets["dev"])
        datasets["test"].data_files_df.split = "test"
    if "dev" not in datasets:
        datasets["dev"] = deepcopy(datasets["test"])
        datasets["dev"].data_files_df.split = "dev"

    # Combine the Highlighter Datasets together because this is what the YoloWriter
    # expects
    combined_ds = datasets["train"]
    combined_ds.append([datasets["dev"], datasets["test"]], drop_duplicates_keep="last")

    # Ultralytics name their dataset splits differently so
    # we need to map them
    #   their "val" is our "test"
    #   their "test" is our "dev"
    combined_ds.data_files_df.loc[combined_ds.data_files_df.split == "test", "split"] = "val"
    combined_ds.data_files_df.loc[combined_ds.data_files_df.split == "dev", "split"] = "test"
    return combined_ds


def _make_classify_artefact(onnx_filepath, cfg, crop_args) -> Path:
    d = dict(
        file_url=str(Path(onnx_filepath.absolute())),
        type="OnnxOpset14",
        inference_config=dict(
            type="classifier",
            code="BoxClassifier",
            machine_agent_type_id="d4787671-3839-4af9-9b34-a686faafbfae",
            parameters=dict(
                output_format="yolov8_cls",
                cropper=crop_args.model_dump(),
            ),
        ),
        training_config=cfg,
    )

    artefact_path = onnx_filepath.parent / "artefact.yaml"
    with artefact_path.open("w") as f:
        yaml.dump(d, f)

    return artefact_path


def _make_detect_segment_artefact(onnx_filepath, cfg) -> Path:
    output_format = "yolov8_seg" if cfg["task"] == "segment" else "yolov8_det"
    d = dict(
        file_url=str(Path(onnx_filepath.absolute())),
        type="OnnxOpset14",
        inference_config=dict(
            type="detector",
            code="Detector",
            machine_agent_type_id="29653174-8f45-440d-b75a-4ed0aa5fa6ff",
            parameters=dict(
                output_format=output_format,
            ),
        ),
        training_config=cfg,
    )

    artefact_path = onnx_filepath.parent / "artefact.yaml"
    with artefact_path.open("w") as f:
        yaml.dump(d, f)

    return artefact_path


def make_artefact(model, cfg, crop_args) -> Path:
    # Disable ultralyitcs' auto install of packages
    ultralytics.utils.checks.AUTOINSTALL = False
    onnx_filepath = Path(model.export(format="onnx", batch=1, dynamic=False, device=0))

    if cfg["task"] == "classify":
        return _make_classify_artefact(onnx_filepath, cfg, crop_args)
    elif cfg["task"] in ("detect", "segment"):
        return _make_detect_segment_artefact(onnx_filepath, cfg)


def train(cfg, training_run_dir: Path, crop_args: Optional[CropArgs]):
    model = ultralytics.YOLO(cfg["model"])

    ultralytics.settings.update({"datasets_dir": str(training_run_dir.absolute())})

    data_cfg_path = (training_run_dir / "datasets" / "data.yaml").absolute()
    with data_cfg_path.open("r") as f:
        data_cfg = yaml.safe_load(f)

    with data_cfg_path.open("w") as f:
        yaml.dump(data_cfg, f)

    if cfg["task"] == "classify":
        cfg["data"] = str(data_cfg_path.parent)
    else:
        cfg["data"] = str(data_cfg_path)
        cfg["single_cls"] = data_cfg["nc"] == 1
        cfg["classes"] = list(data_cfg["names"].keys())

    model.train(**cfg)
    artefact_path = make_artefact(model, cfg, crop_args)

    return model, artefact_path.absolute()


def export(checkpoint, cfg, training_run_dir, crop_args, cfg_overrides={}):

    if isinstance(cfg, (str, Path)):
        with open(cfg, "r") as f:
            cfg = yaml.safe_load(f)

    cfg["model"] = checkpoint
    cfg.update(cfg_overrides)
    model = ultralytics.YOLO(cfg["model"])
    artefact_path = make_artefact(model, cfg, crop_args)

    return artefact_path.absolute()
