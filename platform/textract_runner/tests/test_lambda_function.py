"""
Unit tests for textract_runner lambda function using moto
"""

import json
from typing import Callable
from unittest import mock
import pytest
import boto3
from moto import mock_aws
from ..app import lambda_function as sut

BUCKET = "textract-lambda-test-bucket"
DOCUMENT_KEY = "documents/test-doc.pdf"
MOCK_TEXTRACT_RESPONSE = {
    "DocumentMetadata": {"Pages": 1},
    "Blocks": [
        {
            "BlockType": "LINE",
            "Text": "This is a test document.",
            "Confidence": 99.0,
        }
    ],
}


@pytest.fixture(autouse=True)
def _moto_setup():
    """Create a mocked S3 client."""
    with mock_aws():
        region = boto3.Session().region_name
        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": region}
        )

        s3.put_object(
            Bucket=BUCKET,
            Key=DOCUMENT_KEY,
            Body=b"fake pdf content",
        )

        yield  # keep using moto context for tests


@pytest.fixture(name="mock_textract_client", autouse=True)
def _mock_textract_client():
    """Mock Textract client to return a fixed response."""

    mock_client = mock.Mock()
    mock_client.analyze_document.return_value = MOCK_TEXTRACT_RESPONSE

    with mock.patch.object(
        sut, sut._textract_client.__name__, return_value=mock_client
    ):
        yield mock_client


def _valid_config(textract_config: sut.TextractConfig | None = None) -> sut.Payload:
    return {
        "bucket": BUCKET,
        "key": DOCUMENT_KEY,
        "results_key": "results/test-doc-results.json",
        "textract_config": (textract_config or {"feature_types": ["TABLES", "FORMS"]}),
    }


@pytest.mark.parametrize(
    "textract_config",
    [
        {},  # test passes with unchanged valid config
        {"feature_types": ["QUERIES"], "queries": {"tq1": "What is the total amount?"}},
        {
            "feature_types": ["FORMS", "QUERIES"],
            "queries": {
                "tq1": "What is your favourite colour?",
                "tq2": "What is your favourite animal?",
            },
        },
    ],
)
def test_lambda_handler_success(
    mock_textract_client, textract_config: sut.TextractConfig
):
    """Test successful lambda execution with valid payload."""
    payload = _valid_config(textract_config)

    result = sut.lambda_handler(payload, None)

    assert result == {"status": "success"}

    # Verify results were written to S3
    s3 = boto3.client("s3", region_name="us-east-1")
    response = s3.get_object(Bucket=BUCKET, Key=payload["results_key"])
    results = json.loads(response["Body"].read().decode("utf-8"))

    assert results == MOCK_TEXTRACT_RESPONSE

    textract_params = mock_textract_client.analyze_document.call_args.kwargs
    assert textract_params["Document"]["S3Object"] == {
        "Bucket": BUCKET,
        "Name": DOCUMENT_KEY,
    }
    assert set(textract_params["FeatureTypes"]) == set(
        payload["textract_config"]["feature_types"]
    )

    if "QUERIES" in payload["textract_config"]["feature_types"]:
        assert len(textract_params["QueriesConfig"]["Queries"]) == len(
            payload["textract_config"].get("queries", {})
        )
    else:
        assert "QueriesConfig" not in textract_params


@pytest.mark.parametrize(
    "deleter",
    [
        pytest.param(lambda d: d.pop("bucket"), id="missing bucket"),
        pytest.param(lambda d: d.pop("key"), id="missing key"),
        pytest.param(lambda d: d.pop("results_key"), id="missing results_key"),
        pytest.param(lambda d: d.pop("textract_config"), id="missing textract_config"),
        pytest.param(
            lambda d: d["textract_config"].pop("feature_types"),
            id="missing textract_config.feature_types",
        ),
    ],
)
def test_lambda_handler_missing_keys(deleter: Callable):
    """Test lambda returns error status when config is missing."""

    payload = _valid_config()
    deleter(payload)

    result = sut.lambda_handler(payload, None)

    assert result["status"] == "error"
    assert "Missing required key" in result["error_reason"]


@pytest.mark.parametrize("queries", [None, {}])
def test_lambda_handler_no_query_definitions(queries: dict | None):
    """Test lambda returns error status when QUERIES in feature_types
    but no queries provided."""

    payload: sut.Payload = {
        "bucket": BUCKET,
        "key": DOCUMENT_KEY,
        "results_key": "results/test.json",
        "textract_config": {"feature_types": ["QUERIES"], "queries": queries},
    }

    result = sut.lambda_handler(payload, None)
    assert result["status"] == "error"
    assert "Missing 'queries'" in result["error_reason"]


def test_lambda_handler_nested_s3_paths():
    """Test handling documents with nested S3 paths."""
    s3 = boto3.client("s3", region_name="us-east-1")

    doc_key = "uploads/2026/02/10/user123/document.pdf"
    result_key = "results/2026/02/10/user123/document-results.json"

    s3.put_object(Bucket=BUCKET, Key=doc_key, Body=b"fake content")

    payload: sut.Payload = {
        "bucket": BUCKET,
        "key": doc_key,
        "results_key": result_key,
        "textract_config": {
            "feature_types": ["FORMS"],
        },
    }

    result = sut.lambda_handler(payload, None)

    assert result == {"status": "success"}

    # Verify results were stored at correct path
    response = s3.get_object(Bucket=BUCKET, Key=result_key)
    results = json.loads(response["Body"].read().decode("utf-8"))
    assert results == MOCK_TEXTRACT_RESPONSE
