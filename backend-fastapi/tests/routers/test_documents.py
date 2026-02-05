"""tests for routers/document.py"""

import json
from unittest import mock

from fastapi.testclient import TestClient

from userdb.aws.s3 import UploadInfo
from userdb.routers import documents as doc_router
from userdb.utils import auth
from tests.conftest import FakeRedis


def test_uploads_presign_endpoint(
    app: TestClient, default_user: auth.CurrentUser, fake_redis: FakeRedis
):
    """test /document/presign endpoint generates and returns a presigned upload url"""
    upload = UploadInfo(
        upload_id="someid",
        upload_url=f"https://s3.example/{default_user.username}/doc.txt",
        object_key="somekey",
    )

    assert not fake_redis.get("upload:someid")

    with mock.patch.object(
        doc_router.s3,
        doc_router.s3.generate_presigned_upload_url.__name__,
        return_value=upload,
    ):
        resp = app.post(
            "/document/presign",
            json={"filename": "doc.txt", "contentType": "text/plain"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("uploadUrl") == upload.upload_url
    assert data.get("uploadId") == upload.upload_id

    cached = fake_redis.get("upload:someid")
    assert cached
    assert isinstance(cached, str)

    cached_data = json.loads(cached)
    assert cached_data["object_key"] == upload.object_key
    assert cached_data["username"] == default_user.username


def test_process_document_success(
    app: TestClient, default_user: auth.CurrentUser, fake_redis: FakeRedis
):
    """test successful /document/{upload_id}/process starts processing"""
    upload_id = "upload123"
    object_key = "my/object/key.pdf"

    fake_redis.set(
        f"upload:{upload_id}",
        json.dumps({"object_key": object_key, "username": default_user.username}),
    )

    with mock.patch.object(
        doc_router.sfn,
        doc_router.sfn.process_document.__name__,
        return_value={
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:stateMachine:execution"
        },
    ) as mock_proc:
        resp = app.post(f"/document/{upload_id}/process")

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "processing_started"
    assert data.get("sfn_response")
    mock_proc.assert_called_once_with(object_key)


def test_process_document_not_found(app: TestClient):
    """test processing a non-existent upload id returns 404"""

    resp = app.post("/document/notfound/process")
    assert resp.status_code == 404
