from pathlib import Path
from typing import Any, List, Optional, Tuple
from uuid import UUID

import ultralytics

from highlighter.client.gql_client import HLClient
from highlighter.client.io import multithread_graphql_file_download
from highlighter.client.training_config import TrainingConfigType
from highlighter.core.const import OBJECT_CLASS_ATTRIBUTE_UUID
from highlighter.datasets.cropping import CropArgs
from highlighter.datasets.dataset import Dataset
from highlighter.datasets.formats.yolo.writer import YoloWriter
from highlighter.trainers import yolov11

__all__ = ["filter_dataset", "train", "evaluate"]

# Only used for classification.
# Modify this to change the cropping behaviour when training a
# a box classifier (a classifier trained on cropped detections)
CROP_ARGS = CropArgs(
    crop_rotated_rect=False,
    scale=None,
    pad=None,
)


def filter_dataset(dataset: Dataset) -> Tuple[Dataset, UUID, Optional[List[Any]]]:
    """Optionally add some code to filter the Highlighter Datasets as required.
    The YoloWriter will only use entities with both a pixel_location attribute
    and a 'category_attribute_id' attribute when converting to the Yolo dataset format.
    It will the unique values for the object_class attribute as the detection
    categories.

    For example, if you want to train a detector that finds Apples and Bananas,
    and your taxonomy looks like this:

        - object_class: Apple
        - object_class: Orange
        - object_class: Banana

    Then you may do something like this:

        adf = combined_ds.annotations_df
        ddf = combined_ds.data_files_df

        orange_entity_ids = adf[(adf.attribute_id == OBJECT_CLASS_ATTRIBUTE_UUID) &
                               (adf.value == "Orange")].entity_id.unique()

        # Filter out offending entities
        adf = adf[adf.entity_id.isin(orange_entity_ids)]

        # clean up images that are no longer needed
        ddf = ddf[ddf.data_file_id.isin(adf.data_file_id)]

        combined_ds.annotations_df = adf
    """
    # Only use attributes with this specific attribute_id as the
    # categories for your dataset
    category_attribute_id: UUID = OBJECT_CLASS_ATTRIBUTE_UUID

    # Optionally define a list of attribute values to use for your dataset.
    # If None, then use all unique attribute_values for the given
    # category_attribute_id as the categories
    categories: Optional[List[Any]] = None
    return dataset, category_attribute_id, categories


def train(training_config: TrainingConfigType, dataset: Dataset, training_run_dir: Path):

    yolo_dataset_dir = training_run_dir / "datasets"

    cfg = ultralytics.cfg.yaml_load("cfg.yaml")

    if cfg["task"] == "classify":
        crop_args = CROP_ARGS
    else:
        crop_args = None

    if not (yolo_dataset_dir / "data.yaml").exists():
        # Optionally filter dataset, see filter_dataset's doc str
        filtered_ds, category_attribute_id, categories = filter_dataset(dataset)

        # Download required images
        image_cache_dir = training_run_dir / "images"
        multithread_graphql_file_download(
            HLClient.get_client(),
            filtered_ds.data_files_df.data_file_id.values,
            image_cache_dir,
        )

        ddf = filtered_ds.data_files_df
        if any([Path(f).suffix.lower() == ".mp4" for f in ddf.filename.unique()]):
            print("Detected video dataset, interpolating data from keyframes")
            filtered_ds = filtered_ds.interpolate_from_key_frames(
                frame_save_dir=image_cache_dir,
                source_video_dir=image_cache_dir,
            )

        # Write dataset in yolo format
        writer = YoloWriter(
            output_dir=yolo_dataset_dir,
            image_cache_dir=image_cache_dir,
            category_attribute_id=category_attribute_id,
            categories=categories,
            task=cfg["task"],
            crop_args=crop_args,
        )
        writer.write(filtered_ds)

    return yolov11.train(cfg, training_run_dir, crop_args)


def evaluate():
    """ToDo"""
    pass
