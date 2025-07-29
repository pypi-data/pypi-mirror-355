import os
import shutil
from pathlib import Path

import click
import yaml

from highlighter.cli.logging import ColourStr
from highlighter.client import TrainingConfigType
from highlighter.client.gql_client import HLClient
from highlighter.datasets.dataset import Dataset
from highlighter.trainers import _scaffold


@click.group("train")
@click.pass_context
def train_group(ctx):
    pass


def _validate_training_run_dir(training_run_dir: Path):
    trainer_py = training_run_dir / "trainer.py"
    if trainer_py.exists():
        return training_run_dir

    ml_training_dir = training_run_dir / "ml_training"
    training_run_dirs = list(ml_training_dir.glob("*"))
    if len(training_run_dirs) == 1:
        return training_run_dirs[0]

    raise ValueError(f"Invalid training_run_dir {training_run_dir}")


@train_group.command("start")
@click.argument("training-run-dir", required=False, default=".")
@click.option("--yes", "-y", is_flag=True, default=False)
@click.pass_context
def train_start(ctx, training_run_dir, yes):
    client: HLClient = ctx.obj["client"]

    training_run_dir = Path(training_run_dir).absolute()
    training_run_dir = _validate_training_run_dir(training_run_dir)
    training_run_id = training_run_dir.stem

    scaffold_dir = training_run_dir.parent.parent

    hl_training_config_json = _scaffold.DIRS.hl_training_config(scaffold_dir, training_run_id)
    highlighter_training_config = TrainingConfigType.from_json(hl_training_config_json)
    dataset_cache_dir = _scaffold.DIRS.hl_training_run_cache_datasets_dir(scaffold_dir, training_run_id)
    datasets = Dataset.read_training_config(client, highlighter_training_config, dataset_cache_dir)

    hl_ctx = _scaffold.load_hl_context(_scaffold.DIRS.hl_context_json(scaffold_dir))
    trainer_type = hl_ctx[f"training_run_{training_run_id}"]["trainer"]

    if "yolo" in trainer_type:
        from highlighter.trainers.yolov11 import prepare_datasets

        combined_ds = prepare_datasets(datasets)
    else:
        raise ValueError(f"Invalid trainer_type '{trainer_type}'")

    if (training_run_dir / "datasets" / "data.yaml").exists() and (
        yes or _scaffold.ask_to_overwrite(training_run_dir / "datasets")
    ):
        click.echo(f"Removing: {training_run_dir / 'datasets'}")
        shutil.rmtree(training_run_dir / "datasets")

    trainer = _scaffold.load_trainer_module(training_run_dir)

    os.chdir(training_run_dir)
    _, artefact_path = trainer.train(highlighter_training_config, combined_ds, training_run_dir)
    click.echo(f"Training {training_run_id} complete")
    cmd = ColourStr.green(
        f"hl training-run artefact create -i {training_run_id} -a {artefact_path.relative_to(training_run_dir)}"
    )
    click.echo(f"Next run: `{cmd}` to upload to Highlighter")


@train_group.command("export")
@click.argument("training-run-dir", required=False, default=".")
@click.argument("checkpoint", required=True, type=click.Path(dir_okay=False))
@click.argument("config", required=True, type=click.Path(dir_okay=False))
@click.pass_context
def train_export(ctx, training_run_dir, checkpoint, config):
    training_run_dir = Path(training_run_dir).absolute()
    training_run_dir = _validate_training_run_dir(training_run_dir)
    training_run_id = training_run_dir.stem

    scaffold_dir = training_run_dir.parent.parent

    hl_ctx = _scaffold.load_hl_context(_scaffold.DIRS.hl_context_json(scaffold_dir))
    trainer_type = hl_ctx[f"training_run_{training_run_id}"]["trainer"]

    trainer = _scaffold.load_trainer_module(training_run_dir)
    crop_args = getattr(trainer, "CROP_ARGS", None)

    if "yolo" in trainer_type:
        from highlighter.trainers.yolov11 import export

        artefact_path = export(checkpoint, config, training_run_dir, crop_args)
    else:
        raise ValueError(f"Unable to determine trainer from '{trainer_type}'")

    click.echo(f"Export {checkpoint} complete")
    cmd = ColourStr.green(
        f"hl training-run artefact create -i {training_run_id} -a {artefact_path.relative_to(Path.cwd())}"
    )
    click.echo(f"Next run: `{cmd}` to upload to Highlighter")
