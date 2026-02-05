"""Tests for the object check lambda handler."""

import pytest

import boto3
from moto import mock_aws

from ..app import lambda_function

BUCKET = "test-bucket"
RAW_KEY = "uploads/raw/user1/test-file.txt"
CLEAN_KEY = "uploads/clean/user1/test-file.txt"


@pytest.fixture(name="s3", autouse=True)
def _s3():
    with mock_aws():
        region = boto3.Session().region_name
        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": region}
        )
        yield s3


@pytest.mark.parametrize(
    "malware_status, expect_ok",
    [
        ("NO_THREATS_FOUND", True),
        ("THREATS_FOUND", False),
        ("UNSUPPORTED", False),
        ("ACCESS_DENIED", False),
        ("FAILED", False),
    ],
)
def test_lambda_handler_malware(s3, malware_status: str, expect_ok: bool):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    s3.put_object(Bucket=BUCKET, Key=RAW_KEY, Body=png_bytes)
    s3.put_object_tagging(
        Bucket=BUCKET,
        Key=RAW_KEY,
        Tagging={
            "TagSet": [{"Key": "GuardDutyMalwareScanStatus", "Value": malware_status}]
        },
    )

    payload = {"bucket": BUCKET, "key": RAW_KEY}
    result = lambda_function.lambda_handler(payload, context={})

    keys = s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    assert len(keys) == 1

    if expect_ok:
        assert result == {"file_ok": True, "new_key": CLEAN_KEY}
        assert keys[0]["Key"] == CLEAN_KEY
    else:
        assert result == {"file_ok": False, "reason": "virus_detected_or_scan_failed"}
        assert keys[0]["Key"] == RAW_KEY


@pytest.mark.parametrize(
    "file_content, expect_ok",
    [
        pytest.param(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, True, id="png"),
        pytest.param(b"%PDF-1.4\n%..." + b"\x00" * 100, True, id="pdf"),
        pytest.param(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100, True, id="jpeg"),
        pytest.param(b"just some text", False, id="plaintext"),
        pytest.param(b"PK\x03\x04", False, id="zip"),
    ],
)
def test_lambda_handler_filetype(s3, file_content: bytes, expect_ok: bool):
    s3.put_object(Bucket=BUCKET, Key=RAW_KEY, Body=file_content)
    s3.put_object_tagging(
        Bucket=BUCKET,
        Key=RAW_KEY,
        Tagging={
            "TagSet": [
                {"Key": "GuardDutyMalwareScanStatus", "Value": "NO_THREATS_FOUND"}
            ]
        },
    )

    payload = {"bucket": BUCKET, "key": RAW_KEY}
    result = lambda_function.lambda_handler(payload, context={})

    if expect_ok:
        assert result == {"file_ok": True, "new_key": CLEAN_KEY}
    else:
        assert result == {
            "file_ok": False,
            "reason": "invalid_file_type",
        }


def test_file_not_found():
    payload = {"bucket": BUCKET, "key": RAW_KEY}
    result = lambda_function.lambda_handler(payload, context={})

    assert result == {"file_ok": False, "reason": "file_not_found"}
