"""Methods for AWS S3 interactions."""

import functools
import re
import uuid
import boto3
import os

from userdb.models.document import DocumentPresignRequest
from userdb.utils.auth import CurrentUser

PRESIGN_EXPIRY_SECONDS = 60


@functools.lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "s3",
        region_name=os.environ["AWS_REGION"],
    )


def _create_object_key(user: CurrentUser, upload_id: uuid.UUID, filename: str) -> str:
    """Create a unique S3 object key with sanitised filename for the user's upload."""

    sanitised_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    sanitised_filename = re.sub(r"_+", "_", sanitised_filename)
    sanitised_filename = sanitised_filename.lower()[:100]

    return (
        os.environ["UPLOAD_PATH_PREFIX"]
        + f"/{user.username}/{upload_id}_{sanitised_filename}"
    )


class UploadInfo:
    """Information about a presigned upload URL."""

    def __init__(self, *, upload_id: str, upload_url: str, object_key: str):
        self.upload_id = upload_id
        self.upload_url = upload_url
        self.object_key = object_key


def generate_presigned_upload_url(
    user: CurrentUser, file_info: DocumentPresignRequest
) -> UploadInfo:
    """Generate a presigned S3 upload URL for the given user."""
    upload_id = uuid.uuid4()
    object_key = _create_object_key(user, upload_id, file_info.filename)
    presigned_url = _client().generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": os.environ["UPLOAD_BUCKET_NAME"],
            "Key": object_key,
            "ContentType": file_info.content_type,
        },
        ExpiresIn=PRESIGN_EXPIRY_SECONDS,
    )

    return UploadInfo(
        upload_url=presigned_url,
        object_key=object_key,
        upload_id=str(upload_id),
    )


def get_object(bucket: str, key: str) -> str:
    """Get an object from S3 and return its content."""
    response = _client().get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")
