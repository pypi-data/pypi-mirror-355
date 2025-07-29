from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ..core import GQLBaseModel
from .gql_client import HLClient

__all__ = [
    "EvaluationMetric",
    "EvaluationMetricCodeEnum",
    "EvaluationMetricResult",
    "create_evaluation_metric",
    "create_evaluation_metric_result",
    "find_or_create_evaluation_metric",
]


class EvaluationMetricCodeEnum(str, Enum):
    Dice = "Dice"
    mAP = "mAP"
    MaAD = "MaAD"
    MeAD = "MeAD"
    Other = "Other"
    AP = "AP"


class EvaluationMetric(GQLBaseModel):
    model_config = ConfigDict(use_enum_values=True)

    research_plan_id: int
    code: EvaluationMetricCodeEnum
    chart: Optional[str] = None
    description: Optional[str] = None
    iou: Optional[float] = None
    name: str
    object_class_uuid: Optional[Union[UUID, str]] = None
    weighted: Optional[bool] = False
    id: Optional[int] = None

    def dict(self, *args, **kwargs):
        d = super().model_dump(*args, **kwargs)
        if "object_class_uuid" in d:
            d["object_class_uuid"] = str(d["object_class_uuid"])
        return d


class EvaluationMetricResult(GQLBaseModel, extra="forbid"):
    research_plan_metric_id: int
    result: float
    # iso datetime str will be generated at instantiation
    # if not supplied manually.
    occured_at: Optional[Union[datetime, str]] = Field(..., default_factory=datetime.now)
    object_class_uuid: Optional[Union[UUID, str]] = None
    training_run_id: Optional[int] = None

    @field_validator("occured_at", mode="before")
    def set_timestamp(cls, v):
        if v is None:
            v = datetime.utcnow().isoformat()
        elif isinstance(v, str):
            v = datetime.fromisoformat(v).isoformat()
        elif isinstance(v, datetime):
            v = v.isoformat()
        else:
            raise ValidationError()
        return v

    @classmethod
    def from_yaml(cls, path: Union[Path, str]):
        path = Path(path)
        with path.open("r") as f:
            data = yaml.safe_load(f)
        return cls(**data)


def get_existing_evaluation_metrics(client: HLClient, evaluation_id: int):
    class QueryReturnType(GQLBaseModel):
        research_plan_metrics: List[EvaluationMetric]

    query_return_type: QueryReturnType = client.researchPlan(return_type=QueryReturnType, id=evaluation_id)

    return query_return_type.research_plan_metrics


def create_evaluation_metric(
    client: HLClient,
    evaluation_id: int,
    code: Union[EvaluationMetricCodeEnum, str],
    name: str,
    description: Optional[str] = None,
    iou: Optional[float] = None,
    weighted: Optional[bool] = False,
    object_class_uuid: Optional[Union[UUID, str]] = None,
) -> EvaluationMetric:
    # ToDo: Have the GQL accept s uuid not an id
    if isinstance(object_class_uuid, UUID):
        object_class_uuid = str(object_class_uuid)

    code = EvaluationMetricCodeEnum(code) if isinstance(code, str) else code

    class CreateResearchPlanMetricReturnType(GQLBaseModel):
        errors: Any = None
        research_plan_metric: Optional[EvaluationMetric] = None

    kwargs = EvaluationMetric(
        research_plan_id=evaluation_id,
        code=code,
        name=name,
        description=description,
        iou=iou,
        weighted=weighted,
        object_class_uuid=object_class_uuid,
    ).gql_dict()

    result = client.createResearchPlanMetric(
        return_type=CreateResearchPlanMetricReturnType, **kwargs
    ).research_plan_metric
    assert result is not None
    return result


def find_or_create_evaluation_metric(
    client: HLClient,
    evaluation_id: int,
    code: Union[EvaluationMetricCodeEnum, str],
    name: str,
    description: Optional[str] = None,
    iou: Optional[float] = None,
    weighted: Optional[bool] = False,
    object_class_uuid: Optional[Union[UUID, str]] = None,
) -> Tuple[EvaluationMetric, bool]:
    existing_evaluation_metrics = {r.name: r for r in get_existing_evaluation_metrics(client, evaluation_id)}

    if name in existing_evaluation_metrics:
        found = True
        result = existing_evaluation_metrics[name]
    else:
        found = False
        result = create_evaluation_metric(
            client,
            evaluation_id,
            code,
            name,
            description=description,
            iou=iou,
            weighted=weighted,
            object_class_uuid=object_class_uuid,
        )
    return result, found


def create_evaluation_metric_result(
    client: HLClient,
    evaluation_metric_id: int,
    result: Union[float, int],
    occured_at: Optional[Union[datetime, str]] = None,
    object_class_uuid: Optional[Union[str, UUID]] = None,
    training_run_id: Optional[int] = None,
):
    """Create an evaluation_metric if it does not exist, optionally
    create an evaluation_metric_result if result is not None
    """
    evaluation_metric_result = EvaluationMetricResult(
        research_plan_metric_id=evaluation_metric_id,
        result=result,
        occured_at=occured_at,
        object_class_uuid=object_class_uuid,
        training_run_id=training_run_id,
    )

    class CreateExperimentResultReturnType(BaseModel):
        errors: Any
        experimentResult: EvaluationMetricResult

    mutation_result: CreateExperimentResultReturnType = client.createExperimentResult(
        return_type=CreateExperimentResultReturnType,
        **evaluation_metric_result.gql_dict(),
    )
    return mutation_result.experimentResult
