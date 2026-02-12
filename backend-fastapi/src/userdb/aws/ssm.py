"""AWS Parameter Store utilities"""

from enum import StrEnum
import functools
import os
import boto3


class Parameter(StrEnum):
    """Enum of AWS Parameter Store parameter names."""

    DOCUMENTS_BUCKET_NAME = "/userdb/documents-bucket-name"
    STEP_FUNCTION_ARN = "/userdb/process-document-step-function-arn"


@functools.lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "ssm",
        region_name=os.environ["AWS_REGION"],
    )


@functools.lru_cache(maxsize=sum(1 for _ in Parameter))
def get_parameter(name: Parameter) -> str:
    """Get a parameter value from AWS Parameter Store."""
    response = _client().get_parameter(Name=name)
    return response["Parameter"]["Value"]
