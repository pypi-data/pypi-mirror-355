"""
For video streams:
- Collect the inferred entities in memory until the end of the stream
- At the end of the stream, create an Avro file on S3 with the annotations and observations
- Finally create a submission pointing to the Avro file
For single image and text file streams:
- Create a submission storing the annotations and observations in the database
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel

import highlighter as hl
from highlighter import DataFile, Entity
from highlighter.agent.capabilities import Capability, StreamEvent, StreamState
from highlighter.agent.capabilities.base_capability import VIDEO
from highlighter.agent.utilities import (
    EntityAggregator,
    FileAvroEntityWriter,
    S3AvroEntityWriter,
)
from highlighter.client import HLClient


class CreateSubmissionPayload(BaseModel):
    errors: List[str]


class AssessmentWrite(Capability):
    def __init__(self, context):
        super().__init__(context)
        self.client = HLClient.get_client()
        self.entity_agg = EntityAggregator()
        self.debug = False

    def process_frame(self, stream, data_files: List[DataFile], **kwargs) -> Tuple[StreamEvent, dict]:
        debug, found = self.get_parameter("debug")
        self.debug = debug if found else False
        minimum_track_frame_length, found = self.get_parameter("minimum_track_frame_length")
        if not found:
            minimum_track_frame_length = 0
        self.entity_agg._minimum_track_frame_length = minimum_track_frame_length

        entities = {
            entity_id: entity for entities in kwargs.values() for entity_id, entity in entities.items()
        }

        data_file_ids = [df.file_id for df in data_files]
        stream_media_type = stream.variables["stream_media_type"]
        if stream_media_type != VIDEO:
            task_id = stream.stream_id  # hl_agent.py sets the stream ID to the task ID
            create_submission_from_entities(
                client=self.client,
                entities=entities,
                data_file_ids=data_file_ids,
                task_id=task_id,
            )
            self.logger.info(f"Created submission for task {task_id}")
        else:
            self.entity_agg.append_entities(list(entities.values()))
        self.logger.debug(f"ProcessFrame: {self.__class__.__name__}")

        return StreamEvent.OKAY, {}

    def stop_stream(self, stream, stream_id):
        now_str = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        task_id = stream_id  # hl_agent.py sets the stream ID to the task ID

        if stream.state == StreamState.ERROR:
            diagnostic = f"Stream '{stream_id}' stopped with error condition, not creating submission"
            self.logger.info(diagnostic)
            return StreamEvent.ERROR, {"diagnostic": diagnostic}

        if "stream_media_type" not in stream.variables:
            raise ValueError("The stream was not successfully created")

        if stream.variables["stream_media_type"] != VIDEO:
            pass
        elif self.debug:
            output_filename = f"{task_id}_{now_str}_DEBUG.avro"
            entity_writer = FileAvroEntityWriter(
                hl.ENTITY_AVRO_SCHEMA,
                output_filename,
            )
            entity_writer.write(self.entity_agg._track_entities)
        else:
            output_filename = f"{task_id}_{now_str}.avro"
            entity_writer = S3AvroEntityWriter(
                hl.ENTITY_AVRO_SCHEMA,
                output_filename,
                self.client,
            )

            shrine_file = entity_writer.write(self.entity_agg._track_entities)

            data_file_ids = stream.variables["video_data_file_ids"]
            create_submission_payload = self.client.createSubmission(
                return_type=CreateSubmissionPayload,
                status="completed",
                taskId=task_id,
                backgroundInfoLayerFileData=shrine_file,
                dataFileIds=[str(id) for id in data_file_ids],
            )
            if len(create_submission_payload.errors) > 0:
                diagnostic = str(create_submission_payload.errors)
                self.logger.error(diagnostic)
                return StreamEvent.ERROR, {"diagnostic": diagnostic}
            self.logger.info(f"Created submission for task {task_id} with backgroundInfoLayerFileData")
        return StreamEvent.OKAY, {}


def create_submission_from_entities(
    client: HLClient,
    entities: Dict[UUID, Entity],
    data_file_ids: List[UUID],
    task_id: Optional[UUID],
):
    annotations_attributes = []
    eavt_attributes = []
    for entity in entities.values():
        for annotation in entity.annotations:
            annotations_attributes.append(annotation.gql_dict())
            for eavt in annotation.observations:
                eavt_attributes.append({**eavt.gql_dict(), "annotationUuid": str(annotation.id)})
        for eavt in entity.global_observations:
            eavt_attributes.append(eavt.gql_dict())
    result = client.createSubmission(
        return_type=CreateSubmissionPayload,
        imageUuid=str(data_file_ids[0]),
        status="completed",
        taskId=str(task_id),
        annotationsAttributes=annotations_attributes,
        eavtAttributes=eavt_attributes,
        dataFileIds=[str(id) for id in data_file_ids],
    )
    if len(result.errors) > 0:
        raise ValueError(f"GraphQL Error: {result.errors}")
