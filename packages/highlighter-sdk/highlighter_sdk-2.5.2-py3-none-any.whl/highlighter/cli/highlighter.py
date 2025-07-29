import os
from pathlib import Path

import click

from ..cli import configure_root_logger, get_default_logger
from ..client import HLClient
from ..client.gql_client import (
    CONST_DEFAULT_GRAPHQL_PROFILES_YAML,
    ENV_HL_WEB_GRAPHQL_API_TOKEN,
    ENV_HL_WEB_GRAPHQL_ENDPOINT,
)
from .agent import agent_group
from .assessment import assessment_group
from .config import config_group
from .data_files import data_file_group
from .dataset import dataset_group
from .evaluation import evaluation_group
from .experiment import experiment_group
from .object_class import object_class_group
from .step import step_group
from .task import task_group
from .template import generate_group, new_cmd
from .trainer import train_group
from .training_run import training_run_group


class NoHLClientCredentialsError(Exception):
    def __init__(self):
        message = (
            "\nNo way of determining credentials for HLClient "
            "could be found. \n"
            "\tOption 1: Use the --profile flag in the cli\n"
            "\tOption 2: Use the --api-token and --endpoint-url flags in the cli\n"
            "\tOption 3: export environment variables"
        )
        super().__init__(message)


class NoHLClient:
    """
    Fallback class for when a user does not provide a way
    of deterimining Highlighter credentials. This allows them
    to run help commands and other commands like 'config' that
    do not rely on a working HLClient, but will give a nice
    error message when they do.
    """

    def __getattr__(self, key):
        raise NoHLClientCredentialsError()

    def __repr__(self):
        return "NoHLClient"


@click.group("highlighter")
@click.option("--api-token", type=str)
@click.option("--endpoint-url", type=str)
@click.option("--profile", type=str, default=None)
@click.option("--profiles-path", type=str, default=CONST_DEFAULT_GRAPHQL_PROFILES_YAML)
@click.pass_context
def highlighter_group(ctx, api_token, endpoint_url, profile, profiles_path):
    configure_root_logger(Path.home() / ".highlighter" / "log" / "development.log")
    logger = get_default_logger(__name__)

    if profile is not None:
        client = HLClient.from_profile(profile=profile)
    elif (endpoint_url is not None) and (api_token is not None):
        client = HLClient.from_credential(
            api_token=api_token,
            endpoint_url=endpoint_url,
        )
    elif ENV_HL_WEB_GRAPHQL_ENDPOINT in os.environ:
        client = HLClient.get_client()
    else:
        client = NoHLClient()

    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj.update({"client": client})
    logger.debug(f"HLClient: {client}")


@highlighter_group.command("write")
@click.argument("outfile", type=str)
@click.pass_context
def write(ctx, outfile):
    """Write credentials to a file.

    Each credential is appended to the given file.

    eg: highlighter-v2 --profile abc .envrc

    Results in the following lines being appended
    the .envrc

    export HL_WEB_GRAPHQL_ENDPOINT=...
    export HL_WEB_GRAPHQL_API_TOKEN=...
    """
    client = ctx.obj["client"]
    client.append_credentials_to_env_file(outfile)


@highlighter_group.command("export")
@click.pass_context
def export(ctx):
    """Export a profile's credentials to env

    Wrap this command in `back ticks` to export a profile's credentials to
    your environment

    eg: `highlighter-v2 --profile abc export`

    Results in the following credentials being
    added to your environment variables

    HL_WEB_GRAPHQL_ENDPOINT=...
    HL_WEB_GRAPHQL_API_TOKEN=...
    """
    client = ctx.obj["client"]

    click.echo("Wrap the command in `back ticks` to execute the exports", err=True)
    click.echo(
        f"export {ENV_HL_WEB_GRAPHQL_ENDPOINT}={client.endpoint_url} {ENV_HL_WEB_GRAPHQL_API_TOKEN}={client.api_token}"
    )


highlighter_group.add_command(new_cmd)
highlighter_group.add_command(agent_group)
highlighter_group.add_command(assessment_group)
highlighter_group.add_command(config_group)
highlighter_group.add_command(data_file_group)
highlighter_group.add_command(dataset_group)
highlighter_group.add_command(experiment_group)
highlighter_group.add_command(object_class_group)
highlighter_group.add_command(step_group)
highlighter_group.add_command(task_group)
highlighter_group.add_command(training_run_group)
highlighter_group.add_command(evaluation_group)
highlighter_group.add_command(generate_group)
highlighter_group.add_command(train_group)


if __name__ == "__main__":
    highlighter_group()
