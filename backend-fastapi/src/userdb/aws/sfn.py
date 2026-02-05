"""AWS Step Functions methods."""

import asyncio
import functools
import json
import boto3
import os

from userdb.aws import s3, textract
from userdb.models.user import ProcessedUserData
from userdb.responses import SuccessResult
from userdb.utils import log

RESULTS_SUFFIX = "-analyzed.json"

_logger = log.get_logger(__name__)


@functools.lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "stepfunctions",
        region_name=os.environ["AWS_REGION"],
    )


async def process_document(object_key: str) -> SuccessResult[ProcessedUserData]:
    """Trigger a Step Functions state machine execution for the given S3 object key."""

    sfn = _client()

    input_payload = {"bucket": os.environ["UPLOAD_BUCKET_NAME"], "key": object_key}

    response = sfn.start_execution(
        stateMachineArn=os.environ.get("DOCUMENT_PROCESSING_SFN_ARN"),
        input=json.dumps(input_payload),
    )

    execution_arn = response["executionArn"]
    _logger.info("Execution ARN: %s", execution_arn)

    while True:
        await asyncio.sleep(1)
        status = sfn.describe_execution(executionArn=execution_arn)["status"]
        if status != "RUNNING":
            break

    if status != "SUCCEEDED":
        return SuccessResult(success=False)

    results_key = (
        os.environ["CLEAN_PATH_PREFIX"]
        + object_key.removeprefix(os.environ["UPLOAD_PATH_PREFIX"])
        + RESULTS_SUFFIX
    )
    textract_results = json.loads(
        s3.get_object(bucket=os.environ["UPLOAD_BUCKET_NAME"], key=results_key)
    )

    return textract.handle_results(textract_results)
