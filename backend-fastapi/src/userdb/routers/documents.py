"""API endpoints for document management."""

import json
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

from userdb import redis as redis_store
from userdb.aws import s3, sfn
from userdb.models.document import DocumentPresignRequest, DocumentPresignResponse
from userdb.responses import SuccessResult
from userdb.utils import auth, log

router = APIRouter()

_logger = log.get_logger(__name__)


@router.post(
    "/document/presign",
    dependencies=[auth.require_admin],
)
async def create_presigned_upload(
    file_info: DocumentPresignRequest = Body(...), user=auth.CURRENT_USER
):
    """Generate a presigned S3 upload URL for the authenticated user."""

    _logger.info(
        "Generating presigned upload URL for user %s, filename: %s, content_type: %s",
        user.username,
        file_info.filename,
        file_info.content_type,
    )

    upload_info = s3.generate_presigned_upload_url(user, file_info)

    try:
        key = f"upload:{upload_info.upload_id}"
        value = json.dumps(
            {"object_key": upload_info.object_key, "username": user.username}
        )
        await redis_store.get_redis().set(key, value, ex=3600)
    except Exception as ex:
        _logger.exception("Failed to persist upload metadata to Redis: %s", ex)
        raise HTTPException(status_code=500, detail="Internal server error") from ex

    return DocumentPresignResponse(
        upload_url=upload_info.upload_url,
        upload_id=upload_info.upload_id,
    )


@router.post(
    "/document/{upload_id}/process",
    dependencies=[auth.require_admin],
)
async def process_document(
    upload_id: str,
) -> JSONResponse:
    """Process a previously uploaded document."""

    upload_info = await redis_store.get_redis().get(f"upload:{upload_id}")

    if not upload_info:
        raise HTTPException(status_code=404, detail="Invalid upload ID")
    try:
        upload_data = json.loads(upload_info)
        object_key = upload_data["object_key"]
        result = await sfn.process_document(object_key)
        return result.response()
    except Exception as ex:  # pylint: disable=broad-exception-caught
        _logger.exception("Error processing document: %s", ex)

    return SuccessResult(success=False).response()
