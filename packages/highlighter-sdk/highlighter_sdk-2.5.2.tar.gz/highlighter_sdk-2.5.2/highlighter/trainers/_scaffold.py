import importlib
import json
from enum import Enum
from pathlib import Path


class TrainerType(str, Enum):
    YOLO_DET = "yolo-det"
    YOLO_SEG = "yolo-seg"
    YOLO_CLS = "yolo-cls"
    # ToDo: Add when the sdk can generate the correct dataset formats
    # YOLO_POSE = "yolo-det"
    # YOLO_OOB = "yolo-det"


class DIRS:

    @staticmethod
    def hl_cache(scaffold_dir: Path) -> Path:
        return scaffold_dir / "highlighter"

    @staticmethod
    def hl_context_json(scaffold_dir: Path) -> Path:
        return DIRS.hl_cache(scaffold_dir) / "context.json"

    @staticmethod
    def hl_training_run_cache_dir(scaffold_dir: Path, training_run_id: str) -> Path:
        """This is for storing non-user facing dataset stuff"""
        return DIRS.hl_cache(scaffold_dir) / "ml_training" / training_run_id

    @staticmethod
    def hl_training_config(scaffold_dir: Path, training_run_id: str) -> Path:
        """This is for storing non-user facing dataset stuff"""
        return DIRS.hl_training_run_cache_dir(scaffold_dir, training_run_id) / "training_config.json"

    @staticmethod
    def hl_training_run_cache_datasets_dir(scaffold_dir: Path, training_run_id: str) -> Path:
        """This is for storing non-user facing dataset stuff"""
        return DIRS.hl_cache(scaffold_dir) / "ml_training" / training_run_id / "datasets"

    @staticmethod
    def training_run_dir(scaffold_dir: Path, training_run_id: str) -> Path:
        """This is for storing user facing dataset stuff"""
        return scaffold_dir / "ml_training" / training_run_id


def load_hl_context(ctx_pth: Path):
    with ctx_pth.open("r") as f:
        ctx = json.load(f)
    return ctx


def append_hl_scaffold_context(scaffold_dir, items):
    ctx_pth = DIRS.hl_context_json(scaffold_dir)
    ctx = load_hl_context(ctx_pth)

    for k, v in items.items():
        if (k in ctx) and (ctx[k] != v):
            raise ValueError(f"Cached value {k}: {ctx[k]} conflicts with new value {v}")
        ctx[k] = v

    with ctx_pth.open("w") as f:
        json.dump(ctx, f, indent=2)


def load_trainer_module(training_run_dir):
    trainer_module_path = training_run_dir / "trainer.py"
    module_name = "trainer"
    spec = importlib.util.spec_from_file_location(module_name, trainer_module_path)
    trainer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trainer)
    return trainer


def ask_to_overwrite(dir, terminate=False):
    overwrite = input(f"Do you want to overwrite '{dir}'? (y/n):").lower() in ("y", "yes")
    if overwrite:
        return True
    if terminate:
        raise SystemExit(f"Terminating, {dir} exists.")
    else:
        return False
