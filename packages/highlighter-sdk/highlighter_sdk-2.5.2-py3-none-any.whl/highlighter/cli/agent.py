import json
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Queue
from urllib.parse import urlparse
from uuid import uuid4

import aiko_services as aiko
import click
from aiko_services.main import DEFAULT_STREAM_ID

from highlighter.agent.agent import (
    HLAgent,
    SExpression,
    set_mock_aiko_messager,
)
from highlighter.cli import configure_root_logger, get_default_logger
from highlighter.client.agents import create_agent_token, create_machine_agent_version
from highlighter.client.base_models.data_file import DataFile
from highlighter.client.tasks import lease_task
from highlighter.core.config import (
    HighlighterRuntimeConfig,
    HighlighterRuntimeConfigError,
)


@click.group("agent")
@click.pass_context
def agent_group(ctx):
    pass


# ToDo: Now that I am not accepting cli passed stream params. Is this needed,
# or is it just handled by the aiko pipeline
def parse_stream_parameters(agent, agent_definition) -> dict:

    stream_parameters = {}
    for node in agent.pipeline_graph.nodes():
        node_name = node.name

        # If default_stream_parameters is not present, we are likely
        # working with an aiko.PipelineElement. In this case, we can assume
        # that parameter validation is handled manually.
        if not hasattr(node.element, "default_stream_parameters"):
            continue

        # Start with in code params
        default_stream_parameters = node.element.default_stream_parameters()

        # Overwite with global pipeline definition params
        global_pipeline_definition_params = {
            k: v
            for k, v in agent_definition.parameters
            if k in node.element.DefaultStreamParameters.model_fields
        }
        default_stream_parameters.update(global_pipeline_definition_params)

        # Overwite with per element pipeline definition paras
        element_definition = [e for e in agent_definition.elements if e.name == node_name][0]
        pipeline_element_definition_params = {
            k.replace(f"{node_name}.", ""): v
            for k, v in element_definition.parameters.items()
            if k.replace(f"{node_name}.", "") in node.element.DefaultStreamParameters.model_fields
        }
        node.element.parameters = pipeline_element_definition_params
        default_stream_parameters.update(pipeline_element_definition_params)

        ele_stream_parameters = node.element.DefaultStreamParameters(**default_stream_parameters).model_dump()

        stream_parameters.update(
            {f"{element_definition.name}.{k}": v for k, v in ele_stream_parameters.items()}
        )

    return stream_parameters


def _reading_raw_data_from_stdin_buffer(input_data, expect_filepaths, seperator):
    return (input_data == "--") and (not sys.stdin.isatty() and (not expect_filepaths))


def _is_url(p):
    return all([urlparse(p), urlparse(p).netloc])


def _read_filepaths(input_data, seperator, encoding):
    """Should this belong in the HLFileDataScheme"""
    if input_data == "--":
        # Read raw bytes from stdin
        byte_input = sys.stdin.buffer.read()
        # Decode bytes to string using specified encoding
        text_input = byte_input.decode(encoding)
        # Split on separator and yield non-empty paths

        inputs = text_input.strip().split(seperator)
    else:
        inputs = input_data

    # Take the first scheme and assume and assume all future schemes are the same
    scheme = None

    sources = []
    for path_url in inputs:
        path_url = path_url.strip()

        if Path(path_url).exists():  # Skip empty strings
            if scheme is None:
                scheme = "file"
            elif scheme != "file":
                raise ValueError("All schemes must be the same expected file")
            sources.append(f"file://{path_url}")
        elif _is_url(path_url):
            if scheme is None:
                scheme = "hlhttp"
            elif scheme != "hlhttp":
                raise ValueError("All schemes must be the same expected hlhttp")
            sources.append(f"hlhttp://{path_url}")
        else:
            raise NotImplementedError()

    assert len(sources) > 0
    return sources


def _set_agent_data_source_stream_parameters(agent, data_sources, stream_parameters):

    data_source_capabilities = agent.get_data_source_capabilities()
    if len(data_source_capabilities) == 1:
        data_source_capability_name = data_source_capabilities[0].name
    elif len(data_source_capabilities) > 1:
        raise NotImplementedError(
            f"hl agent start cannot yet support Agents with multiple DataSource Capabilities, got: {data_source_capabilities}"
        )
    else:
        raise NotImplementedError("hl agent start cannot yet support Agents with no DataSource Capabilities")

    input_name = f"{data_source_capability_name}.data_sources"
    stream_parameters[input_name] = data_sources
    return stream_parameters


def _data_sources_are_specified_in_agent_definition(agent):
    data_source_capabilities = agent.get_data_source_capabilities()
    for data_source_capability in data_source_capabilities:
        if data_source_capability.element.definition.parameters.get("data_sources"):
            return True
    return False


def process_data_sources(
    agent,
    stream_id,
    data_sources,
    _hlagent_cli_runner_queue_response,
    queue_response_max_size=100,
    timeout_secs=60,
):
    stream_parameters: dict = parse_stream_parameters(
        agent.pipeline,
        agent.pipeline_definition,
    )

    stream_parameters["database"] = agent.db

    if data_sources:
        data_source_sexp = SExpression.encode(None, data_sources)
        stream_parameters = _set_agent_data_source_stream_parameters(
            agent, data_source_sexp, stream_parameters
        )

    queue_response = Queue(maxsize=queue_response_max_size)
    agent.pipeline.create_stream(stream_id, parameters=stream_parameters, queue_response=queue_response)
    while True:
        stream_event, result = queue_response.get(timeout=timeout_secs)
        agent.pipeline.logger.debug(f"queue_response size: {queue_response.qsize()}")

        # This should only run if running via the HLAgentCliRunner
        if _hlagent_cli_runner_queue_response is not None:
            _hlagent_cli_runner_queue_response.put((stream_event, result))
            if _hlagent_cli_runner_queue_response.qsize() >= queue_response_max_size:
                raise ValueError(f"_hlagent_cli_runner_queue_response size is > {queue_response_max_size}")

        if stream_event["state"] in [aiko.StreamEvent.STOP, aiko.StreamEvent.ERROR]:
            break


def loop_over_process_frame(agent, stream_id, frame_datas, queue_response):
    # This function can be removed once
    # the issue it's solving is resolved.
    # See to function's doc string for more info
    set_mock_aiko_messager()

    if isinstance(frame_datas, dict):
        frame_datas = [frame_datas]

    stream_parameters: dict = parse_stream_parameters(
        agent.pipeline,
        agent.pipeline_definition,
    )

    agent.pipeline.create_stream(stream_id, parameters=stream_parameters, queue_response=queue_response)
    for frame_id, frame in enumerate(frame_datas):
        stream = {
            "stream_id": stream_id,
            "frame_id": frame_id,
        }

        data_files = [
            DataFile(
                file_id=uuid4(),
                content=frame["content"],
                media_frame_index=0,
                content_type="text",
            )
        ]
        agent.pipeline.process_frame(stream, {"data_files": data_files})
    agent.pipeline.destroy_stream(stream_id)


DEFAULT_FILEPATH_SEPERATOR = "\n"
DEFAULT_CONTENT_SEPERATOR = b"===END=="


@agent_group.command("start")
@click.option(
    "--seperator",
    "-p",
    type=str,
    default=None,
    help="If --expect-filepaths is true the default is '\\n'. Else the the unix file seperator '{DEFAULT_CONTENT_SEPERATOR}'. This parameter is only used for piped inputs, if passing paths directly use spaces to separate paths",
)
@click.option("--expect-filepaths", "-f", is_flag=True, default=False)
@click.option("--step-task-ids", "-t", type=str, default=None, help="comma separate for multiple")
@click.option("--step-id", "-i", type=str, default=None)
@click.option("--stream-id", "-s", type=str, default=DEFAULT_STREAM_ID)
@click.option("--dump-definition", type=str, default=None)
@click.option("--allow-non-machine-user", is_flag=True, default=False)
@click.argument("agent_definition", type=click.Path(dir_okay=False, exists=False))
@click.argument("input_data", nargs=-1, type=click.STRING, required=False)
@click.pass_context
def _start(
    ctx,
    seperator,
    expect_filepaths,
    step_task_ids,
    step_id,
    stream_id,
    dump_definition,
    allow_non_machine_user,
    agent_definition,
    input_data,
):
    """Start a local Highlighter Agent to process data either from your local machine or from Highlighter tasks.

    When processing local files, a single stream is created to process all files.
    The Agent definition must have its first element as a
    DataSourceCapability, such as ImageDataSource, VideoDataSource,
    TextDataSource, JsonArrayDataSource, etc. The examples below assume
    the use of ImageDataSource.

    When processing Highlighter tasks, a single stream is created for each
    task. The Agent definition should use AssessmentRead as the first element in this case.
    Note: When processing tasks, use a GraphQL API key specific to the agent being run. You can
    create this using 'hl agent create-token'.

    Examples:

      \b
      1. Start an agent against a single image path
      \b
        > hl agent start -f agent-def.json images/123.jpg

      \b
      2. Start an agent against a multiple image paths
      \b
        > find images/ -name *.jpg | hl agent start -f agent-def.json

      \b
      3. Cat the contents of an image to an agent
      \b
        > cat images/123.jpg | hl agent start -f agent-def.json

      \b
      4. Pass data directly to process_frame
      \b
        > hl agent start -f agent-def.json '[{"foo": "bar"},{"foo": "baz"}]'

      \b
      5. Process tasks from a Highlighter machine-step, using a local agent definition
      \b
        > STEP_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        > hl agent start agent-def.json --step-id "$STEP_UUID"

      \b
      6. Process tasks from a Highlighter machine-step, using an agent definition from Highlighter
      \b
        > STEP_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        > AGENT_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        > hl agent start "$AGENT_UUID" --step-id "$STEP_UUID"

    """
    # setup default logging

    logger = get_default_logger(__name__)
    logger.info(f"loading configuration...")
    try:
        hl_cfg = HighlighterRuntimeConfig.load()
    except (HighlighterRuntimeConfigError, ValueError) as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during loading configuration: {e}")
        sys.exit(1)

    configure_root_logger(hl_cfg.log_path, hl_cfg.log_level)
    logger = get_default_logger(__name__)

    if not input_data:
        input_data = "--"

    if (seperator is None) and (expect_filepaths):
        seperator = DEFAULT_FILEPATH_SEPERATOR
    elif (seperator is None) and (not expect_filepaths):
        seperator = DEFAULT_CONTENT_SEPERATOR

    if step_id and step_task_ids:
        raise ValueError()

    agent = HLAgent(
        agent_definition,
        dump_definition=dump_definition,
        timeout_secs=hl_cfg.agent.timeout_secs,
        task_lease_duration_secs=hl_cfg.agent.task_lease_duration_secs,
        task_polling_period_secs=hl_cfg.agent.task_polling_period_secs,
    )
    agent.run_in_thread()

    # This should only be populated if running via the HLAgentCliRunner
    _hlagent_cli_runner_queue_response = ctx.obj.get("queue_response", None)

    data_sources = None

    if expect_filepaths:

        data_sources = _read_filepaths(input_data, seperator, "utf-8")

    elif _reading_raw_data_from_stdin_buffer(
        input_data, expect_filepaths, seperator
    ) and not _data_sources_are_specified_in_agent_definition(agent):
        """When reading raw data from the stdin buffer we need to:

        - use the `pipe://` scheme
        - determine the datatype expected by the head DataSource<Capability|PipelineElement>
        - ? force the DataSource<Capability|PipelineElement> to deal with the splitting of the
          buffer into individual files, or do the split here, not sure yet
        """
        data_sources = ["hlpipe://"]

    if step_id:
        agent.poll_for_tasks_loop(step_id, allow_non_machine_user=allow_non_machine_user)
    elif step_task_ids:
        client = ctx.obj["client"]
        for task_id in [t.strip() for t in step_task_ids.split(",")]:
            task = lease_task(
                client,
                task_id=task_id,
                lease_sec=hl_cfg.agent.task_lease_duration_secs,
                set_status_to="RUNNING",
            )
            agent._process_task(task)
    elif data_sources or _data_sources_are_specified_in_agent_definition(agent):
        process_data_sources(
            agent,
            stream_id,
            data_sources,
            _hlagent_cli_runner_queue_response,
            hl_cfg.agent.queue_response_max_size,
            timeout_secs=hl_cfg.agent.timeout_secs,
        )
    else:
        # assume process_frame_data is passed in directly either as a json
        # str in input_data or via sdtin buffer
        # assert False, f"-------------: {input_data}"
        try:
            if input_data == "--":
                frame_datas = json.load(sys.stdin.buffer)
            else:
                frame_datas = json.loads(input_data[0])
        except Exception as e:
            raise ValueError(f"{e} -- {input_data}")
        loop_over_process_frame(agent, stream_id, frame_datas, _hlagent_cli_runner_queue_response)

    agent.stop()


@agent_group.command("create-token")
@click.option("--machine-agent-version-id", type=str)
@click.option("--machine-agent-name", type=str, required=False)
@click.option("--machine-agent-version-name", type=str, required=False)
def _create_token(
    machine_agent_version_id,
    machine_agent_name,
    machine_agent_version_name,
):
    """Create an access token for an agent

    Once an access token has been created, run an agent with that identity by
    setting `HL_WEB_GRAPHQL_API_TOKEN=<new-token>` before running `hl agent start`

    Either provide the ID of the machine-agent-version in Highlighter, or
    specify a new machine-agent name and version-name to create a new machine-agent-version
    for your agent.
    """
    if machine_agent_version_id is None:
        if machine_agent_name is not None or machine_agent_version_name is not None:
            raise ValueError(
                "Must specify either 'machine_agent_token', give a machine-agent version "
                "ID as the agent definition, or specify both 'machine_agent_name' and "
                "'machine_agent_version'"
            )
        machine_agent_version = create_machine_agent_version(machine_agent_name, machine_agent_version_name)
        machine_agent_version_id = machine_agent_version.id
    machine_agent_token = create_agent_token(machine_agent_version_id)
    # Print to stdout rather than log
    print(machine_agent_token)
