import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from tempfile import mkdtemp
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from uuid import UUID

import aiko_services as aiko
import gql
import yaml
from aiko_services.main import aiko as aiko_main
from aiko_services.main import generate, parse

from highlighter import MachineAgentVersion
from highlighter.cli.logging import get_default_logger
from highlighter.client.agents import create_pipeline_instance, update_pipeline_instance
from highlighter.client.base_models.base_models import UserType
from highlighter.client.gql_client import HLClient
from highlighter.client.tasks import (
    Task,
    TaskStatus,
    lease_task,
    lease_tasks_from_steps,
    update_task,
)
from highlighter.core.database.database import Database

__all__ = [
    "HLAgent",
    "set_mock_aiko_messager",
    "SExpression",
]


# The stream timeout counts from the most recent process_frame call in a pipeline
STREAM_TIMEOUT_GRACE_TIME_SECONDS = 20
# The pipeline timeout counts from the most recent frame returned on queue_response
PIPELINE_TIMEOUT_SECONDS = 120
TASK_RE_LEASE_EXPIRY_BUFFER_SECONDS = 20


class SExpression:

    @staticmethod
    def encode(cmd: Optional[str], parameters: Union[Dict, List, Tuple]) -> str:
        if cmd:
            return generate(cmd, parameters)
        else:
            return generate(parameters[0], parameters[1:])

    @staticmethod
    def decode(s: str) -> Any:
        return parse(s)


def load_pipeline_definition(path) -> Dict:
    path = Path(path)
    suffix = path.suffix

    if suffix in (".json",):
        with path.open("r") as f:
            pipeline_def = json.load(f)
    elif suffix in (".yml", ".yaml"):
        with path.open("r") as f:
            pipeline_def = yaml.safe_load(f)
    else:
        raise NotImplementedError(
            f"Unsupported pipeline_definition file, '{path}'." " Expected .json|.yml|.yaml"
        )

    def remove_dict_keys_starting_with_a_hash(data):
        if isinstance(data, dict):
            # Create a new dictionary excluding keys starting with "#"
            return {
                key: remove_dict_keys_starting_with_a_hash(value)
                for key, value in data.items()
                if not key.startswith("#")
            }
        elif isinstance(data, list):
            # If the item is a list, recursively apply the function to each element
            return [remove_dict_keys_starting_with_a_hash(item) for item in data]
        else:
            # If the item is neither a dict nor a list, return it as-is
            return data

    pipeline_def = remove_dict_keys_starting_with_a_hash(pipeline_def)
    return pipeline_def


def _validate_uuid(s):
    try:
        u = UUID(s)
        return u
    except Exception as e:
        return None


def _validate_path(s) -> Optional[Path]:
    try:
        p = Path(s)
        if p.exists():
            return p
    except Exception as e:
        return None


class HLAgent:

    def __init__(
        self,
        pipeline_definition: Union[str, dict, os.PathLike],
        name: Optional[str] = "agent",
        dump_definition: Optional[os.PathLike] = None,
        timeout_secs: Optional[float] = 60.0,
        task_lease_duration_secs: Optional[float] = 60.0,
        task_polling_period_secs: Optional[float] = 5.0,
    ):
        self.logger = get_default_logger(__name__)

        if dump_definition is not None:
            pipeline_path = Path(dump_definition)
        else:
            pipeline_path = Path(mkdtemp()) / "pipeline_def.json"

        self.machine_agent_version_id = None

        if pipeline_definition_path := _validate_path(pipeline_definition):
            definition_dict = load_pipeline_definition(pipeline_definition_path)
            if name is None:
                name = pipeline_definition_path.name

        elif def_uuid := _validate_uuid(pipeline_definition):
            result = HLClient.get_client().machine_agent_version(
                return_type=MachineAgentVersion,
                id=str(def_uuid),
            )
            definition_dict = result.hl_serving_agent_definition
            name = result.title
            self.machine_agent_version_id = def_uuid
        elif isinstance(pipeline_definition, dict):
            if name is None:
                raise ValueError(
                    "If pipeline_definition is a dict you must provide the 'name' arg to HLAgent.__init__"
                )
            definition_dict = pipeline_definition

        else:
            if Path(pipeline_definition).suffix not in (".json", ".yml", ".yaml"):
                raise SystemExit(f"pipeline_definition '{pipeline_definition}' path does not exist")
            else:
                raise SystemExit(f"pipeline_definition '{pipeline_definition}' id does not exist")

        self._dump_definition(definition_dict, pipeline_path)

        parsed_definition = aiko.PipelineImpl.parse_pipeline_definition(pipeline_path)

        init_args = aiko.pipeline_args(
            name,
            protocol=aiko.PROTOCOL_PIPELINE,
            definition=parsed_definition,
            definition_pathname=pipeline_path,
        )
        pipeline = aiko.compose_instance(aiko.PipelineImpl, init_args)

        self.pipeline = pipeline
        self.pipeline_definition = parsed_definition
        self.timeout_secs = timeout_secs
        self.task_lease_duration_secs = task_lease_duration_secs
        self.task_polling_period_secs = task_polling_period_secs

        self.db = Database()

    def get_data_source_capabilities(self) -> List[aiko.source_target.DataSource]:
        data_source_elements = [
            node
            for node in self.pipeline.pipeline_graph.nodes()
            if isinstance(node.element, aiko.source_target.DataSource)
        ]
        return data_source_elements

    def _dump_definition(self, pipeline_def: Dict, path: Path):
        with path.open("w") as f:
            json.dump(pipeline_def, f, sort_keys=True, indent=2)

    def run_in_foreground(self, mqtt_connection_required=False):
        self.pipeline.run(mqtt_connection_required=mqtt_connection_required)

    def run_in_thread(self, mqtt_connection_required=False) -> Thread:
        thread = Thread(
            target=self.run_in_foreground,
            daemon=True,
            kwargs={"mqtt_connection_required": mqtt_connection_required},
        )
        thread.start()
        return thread

    def stop(self):
        self.pipeline.stop()
        while aiko.event.event_loop_running:
            time.sleep(0.01)

    def get_head_data_source_capability(self):
        head_capability = [x for x in self.pipeline.pipeline_graph][0]
        if hasattr(head_capability.element, "_is_data_source"):
            return head_capability
        return None

    def set_callback(self, callback_name: str, callback: Callable):
        setattr(self.pipeline, callback_name, callback)

    def process_frame(self, frame_data, stream_id=0, frame_id=0) -> bool:
        stream = {
            "stream_id": stream_id,
            "frame_id": frame_id,
        }
        return self.pipeline.process_frame(stream, frame_data)

    def poll_for_tasks_loop(self, step_id: Union[str, UUID], allow_non_machine_user: bool = False):
        current_user = HLClient.get_client().current_user(return_type=UserType)
        if current_user.machine_agent_version_id is None and not allow_non_machine_user:
            raise RuntimeError(
                "Running agent as non-machine user. To run the agent as a machine user, use "
                "`hl agent create-token` and set HL_WEB_GRAPHQL_API_TOKEN with the returned value before running `hl agent start. "
                "To run the agent as the current user, pass `allow_non_machine_user=True`."
            )

        step_id = UUID(step_id)

        # Report running agent to hl web
        self.pipeline_instance_id = create_pipeline_instance(
            str(self.machine_agent_version_id),
            str(step_id),
        )
        try:
            while True:
                update_pipeline_instance(self.pipeline_instance_id, status="RUNNING")
                tasks = lease_tasks_from_steps(
                    HLClient.get_client(),
                    [step_id],
                    lease_sec=self.task_lease_duration_secs,
                    count=1,
                )
                for task in tasks:
                    self._process_task(task)
                if len(tasks) == 0:
                    time.sleep(self.task_polling_period_secs)
        except KeyboardInterrupt as e:
            # SIGINT received, agent stopped but not failed
            try:
                update_pipeline_instance(self.pipeline_instance_id, status="STOPPED")
            except gql.transport.exceptions.TransportAlreadyConnected:
                # without asyncio
                client = HLClient.get_client()
                client._async = False
                update_pipeline_instance(self.pipeline_instance_id, status="STOPPED")
            raise e
        except Exception as e:
            update_pipeline_instance(self.pipeline_instance_id, status="FAILED", message=str(e))
            raise e

    def _process_task(self, task: Task):
        self.logger.info(f"Processing task {task.id}")
        stream_id = task.id
        stream_result_queue = Queue()
        self.pipeline.create_stream(
            stream_id,
            parameters=task.parameters,
            queue_response=stream_result_queue,
            grace_time=STREAM_TIMEOUT_GRACE_TIME_SECONDS,
        )
        while True:
            try:
                stream_info, frame_data = stream_result_queue.get(timeout=self.timeout_secs)
            except Empty:
                raise ValueError(
                    "Timeout: Agent has not produced a value for more than " f"{self.timeout_secs} seconds"
                )
            if stream_info["state"] == aiko.StreamEvent.STOP:
                self.logger.info(f"Completed task {task.id}")
                update_task(
                    client=HLClient.get_client(),
                    task_id=task.id,
                    status=TaskStatus.SUCCESS,
                )
                break
            if stream_info["state"] == aiko.StreamEvent.ERROR:
                self.logger.error(f"Error in task {task.id}: {frame_data.get('diagnostic')}")
                update_task(
                    client=HLClient.get_client(),
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    message=frame_data.get("diagnostic"),
                )
                break
            if (
                task.leased_until.timestamp()
                < datetime.now(timezone.utc).timestamp() + TASK_RE_LEASE_EXPIRY_BUFFER_SECONDS
            ):
                # Re-lease task
                self.logger.info(f"Extending lease for task {task.id}")
                task = lease_task(
                    client=HLClient.get_client(),
                    task_id=task.id,
                    lease_sec=self.task_lease_duration_secs,
                )


def set_mock_aiko_messager():
    # ToDo: Chat with Andy about if this is a requirement. The issue is
    # in pipeline.py +999 causes an error because if I use `process_frame`
    # directly, without setting the aiko.message object to something I
    # get an attribute error when .publish is called
    class MockMessage:
        def publish(self, *args, **kwargs):
            pass

        def subscribe(self, *args, **kwargs):
            pass

        def unsubscribe(self, *args, **kwargs):
            pass

    aiko_main.message = MockMessage()
