"""tests for aws/s3.py"""

# pylint: disable=protected-access

import os
import re
from unittest import mock
import uuid

import boto3
import pytest

from userdb.aws import s3
from userdb.models.document import DocumentPresignRequest
from userdb.utils.auth import CurrentUser


def test_generate_presigned_upload_url(default_user: CurrentUser):
    """test generate_presigned_upload_url returns expected UploadInfo"""

    file = DocumentPresignRequest(filename="report.pdf", content_type="application/pdf")

    mock_client = mock.MagicMock()
    mock_client.generate_presigned_url.return_value = "the_url"

    with mock.patch.object(
        s3, s3._client.__wrapped__.__name__, return_value=mock_client
    ):
        info = s3.generate_presigned_upload_url(default_user, file)

    assert re.match(
        rf"test-uploads/{re.escape(default_user.username)}/[0-9a-f-]{{36}}_report\.pdf",
        info.object_key,
    )
    assert info.upload_url == "the_url"


@pytest.mark.parametrize(
    "input_filename,s3_filename",
    [
        ("simple.txt", "simple.txt"),
        ("my document.pdf", "my_document.pdf"),
        ("data (final).csv", "data_final_.csv"),
        ('w\tei"../rd#file@name!.docx', "w_ei_.._rd_file_name_.docx"),
    ],
)
def test_create_object_key(input_filename: str, s3_filename: str):
    """test object key format"""

    with mock.patch.dict(
        os.environ,
        {"UPLOAD_PATH_PREFIX": "upload_PREfix"},
    ):
        uid = uuid.UUID("42845275-f3d0-41cd-aa17-001473b78e5f")

        result = s3._create_object_key(
            CurrentUser(username="alan", roles=[]), uid, input_filename
        )

    assert (
        result
        == f"upload_PREfix/alan/42845275-f3d0-41cd-aa17-001473b78e5f_{s3_filename}"
    )


def test_get_object():
    """test get_object retrieves and decodes S3 object content"""

    region = boto3.Session().region_name
    s3_client = boto3.client("s3", region_name=region)

    s3_client.create_bucket(
        Bucket="test-bucket", CreateBucketConfiguration={"LocationConstraint": region}
    )
    s3_client.put_object(Bucket="test-bucket", Key="test-key", Body=b'{"test": "data"}')

    result = s3.get_object(bucket="test-bucket", key="test-key")

    assert result == '{"test": "data"}'
