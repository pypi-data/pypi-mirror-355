import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import click
from cookiecutter.generate import generate_context
from cookiecutter.main import cookiecutter
from cookiecutter.prompt import prompt_for_config

from highlighter.cli.logging import ColourStr
from highlighter.client import TrainingConfigType
from highlighter.client.gql_client import HLClient
from highlighter.datasets.dataset import Dataset
from highlighter.trainers import _scaffold


@click.command("new")
@click.argument("dest", type=click.Path(dir_okay=True, file_okay=False))
@click.pass_context
def new_cmd(ctx, dest):
    """Create a new Highlighter scaffold directory

    \b
    DEST/
      TITLE/
        highlighter/
          context.json
        pyproject.toml
        README.md
        shell.nix

    """
    dest = Path(dest)
    if not dest.exists():
        dest.mkdir(parents=True)

    template_path = Path(__file__).parent.parent / "templates" / "scaffold"

    # Load the context from the Cookiecutter template
    context = generate_context(context_file=template_path / "cookiecutter.json")
    # Prompt user for inputs
    completed_context = prompt_for_config(context)

    _final_path = dest / completed_context["title_slug"]
    if _final_path.exists():
        raise ValueError(f"{_final_path.absolute()} is already a scaffold")

    final_path = cookiecutter(
        str(template_path), no_input=True, extra_context=completed_context, output_dir=str(dest)
    )

    _scaffold.append_hl_scaffold_context(
        Path(final_path), {"cookiecutter_scaffold_context": completed_context}
    )
    click.echo(f"Project created at {final_path}")


@click.group("generate")
@click.pass_context
def generate_group(ctx):
    pass


def _append_readmes(scaffold_dir, tmp_agent_root):
    with (scaffold_dir / "README.md").open("r") as f:
        scaffold_readme = f.read()

    if not "Run Agent" in scaffold_readme:
        with (tmp_agent_root / "README.md").open("r") as f:
            agent_readme = f.read()

        scaffold_readme = f"{scaffold_readme}\n\n{agent_readme}"

        with (scaffold_dir / "README.md").open("w") as f:
            f.write(scaffold_readme)


def _append_capability_inits(src_init, new_init):
    with new_init.open("r") as f:
        new = f.read()

    if src_init.exists():
        with src_init.open("a") as f:
            f.write(new)
    else:
        src_init.parent.mkdir(exist_ok=True)
        with src_init.open("w") as f:
            f.write(new)


def _move_tmp_dirs(scaffold_dst_dir, tmp_agent_src_dir):
    scaffold_dst_dir.mkdir(exist_ok=True)

    for p in os.listdir(str(tmp_agent_src_dir)):
        dst = scaffold_dst_dir / p
        if dst.exists():
            continue
        src = tmp_agent_src_dir / p
        if Path(src).is_file():
            shutil.copy2(src, dst)


def _remove(filepath):
    print(f"Removing: {filepath}")
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


def _cleanup_test_inputs(scaffold_dst_dir, data_type):
    test_data_files = [
        ("image", "test.png"),
        ("video", "test.mp4"),
        ("text", "test.txt"),
    ]

    for dt, name in test_data_files:
        if data_type == dt:
            continue

        _remove(scaffold_dst_dir / name)


@generate_group.command("agent")
@click.argument("scaffold_dir", type=click.Path(dir_okay=True, file_okay=False))
@click.pass_context
def agent_generate(ctx, scaffold_dir):
    scaffold_dir = Path(scaffold_dir)
    highlighter_dir = _scaffold.DIRS.hl_cache(scaffold_dir)
    if not highlighter_dir.exists():
        raise ValueError(
            f"DEST '{scaffold_dir}' must be an existing highlighter scaffold with a highlighter directory. Create one by running 'hl new'"
        )
    hl_ctx = _scaffold.load_hl_context(_scaffold.DIRS.hl_context_json(scaffold_dir))

    template_path = Path(__file__).parent.parent / "agent" / "template"

    # Load the context from the Cookiecutter template
    context = generate_context(context_file=template_path / "cookiecutter.json")
    # Prompt user for inputs
    completed_context = prompt_for_config(context)
    scaffold_pkg_name = hl_ctx["cookiecutter_scaffold_context"]["title_slug"]
    completed_context["_scaffold_pkg_name"] = scaffold_pkg_name

    with TemporaryDirectory() as tmp:

        final_path = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=completed_context,
            output_dir=tmp,
        )

        _append_readmes(scaffold_dir, Path(final_path))
        _append_capability_inits(
            scaffold_dir / "src" / scaffold_pkg_name / "capabilities" / "__init__.py",
            Path(final_path) / "capabilities" / "__init__.py",
        )
        _move_tmp_dirs(
            scaffold_dir / "src" / scaffold_pkg_name / "capabilities", Path(final_path) / "capabilities"
        )

        _move_tmp_dirs(scaffold_dir / "agents", Path(final_path) / "agents")

        _move_tmp_dirs(scaffold_dir / "inputs", Path(final_path) / "inputs")


@generate_group.command("training-run")
@click.argument("training_run_id", type=int)
@click.argument("trainer", type=click.Choice(list(_scaffold.TrainerType)))
@click.argument("scaffold_dir", type=click.Path(dir_okay=True, file_okay=False))
@click.option("--yes", "-y", is_flag=True, default=False)
@click.pass_context
def train_generate(ctx, training_run_id, trainer, scaffold_dir, yes):
    scaffold_dir = Path(scaffold_dir)
    highlighter_dir = _scaffold.DIRS.hl_cache(scaffold_dir)
    if not highlighter_dir.exists():
        raise ValueError(
            f"DEST '{scaffold_dir}' must be an existing highlighter scaffold with a highlighter directory"
        )

    client: HLClient = ctx.obj["client"]
    highlighter_training_config = TrainingConfigType.from_highlighter(client, training_run_id)

    training_run_dir = _scaffold.DIRS.training_run_dir(scaffold_dir, str(training_run_id))
    hl_training_config_json = _scaffold.DIRS.hl_training_config(scaffold_dir, str(training_run_id))
    if training_run_dir.exists() and (yes or _scaffold.ask_to_overwrite(training_run_dir, terminate=True)):
        click.echo(f"Removing '{training_run_dir}'")
        shutil.rmtree(training_run_dir)
        click.echo(f"Removing '{hl_training_config_json.parent}'")
        shutil.rmtree(hl_training_config_json.parent)

    training_run_dir.mkdir(parents=True, exist_ok=False)
    hl_training_config_json.parent.mkdir(parents=True, exist_ok=False)

    highlighter_training_config.dump("json", hl_training_config_json)

    dataset_cache_dir = _scaffold.DIRS.hl_training_run_cache_datasets_dir(
        scaffold_dir,
        str(training_run_id),
    )
    dataset_cache_dir.mkdir()

    Dataset.read_training_config(client, highlighter_training_config, dataset_cache_dir)

    if "yolo" in trainer:
        from highlighter.trainers.yolov11 import generate
    else:
        raise ValueError(f"Unable to determine trainer from '{trainer}'")

    _scaffold.append_hl_scaffold_context(
        scaffold_dir, {f"training_run_{training_run_id}": {"trainer": trainer}}
    )

    generate(training_run_dir, trainer)
    click.echo(f"{trainer} template generated at {training_run_dir}")
    cmd = ColourStr.green(f"hl train start {training_run_dir}")
    if scaffold_dir.absolute() == Path.cwd():
        click.echo(f"Next, run `{cmd}`")
    else:
        cd_cmd = ColourStr.green(f"cd {scaffold_dir}")
        click.echo(f"Next, `{cd_cmd}` and run `{cmd}`")
