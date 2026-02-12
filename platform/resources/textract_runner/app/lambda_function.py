"""
Lambda handler to validate uploaded files:
- Checks GuardDuty malware scan status via S3 object tags
- Checks file type signature (magic bytes) to ensure it's PDF, JPG, or PNG
"""

import json
from typing import NotRequired, TypedDict
import boto3


ENABLED_FEATURE_TYPES = {"TABLES", "FORMS", "QUERIES"}


class Payload(TypedDict):
    bucket: str
    key: str
    results_key: str
    textract_config: "TextractConfig"


class TextractConfig(TypedDict):
    feature_types: list[str]
    queries: NotRequired[dict[str, str] | None]


def _textract_client():
    return boto3.client("textract")


def _validate_payload(payload: Payload) -> None:
    required_keys = ["bucket", "key", "results_key", "textract_config"]
    for key in required_keys:
        if not payload.get(key):
            raise ValueError(f"Missing required key in payload: {key}")

    tc = payload["textract_config"]
    required_tc_keys = ["feature_types"]
    for key in required_tc_keys:
        if not tc.get(key):
            raise ValueError(f"Missing required key in textract_config: {key}")

    unsupported_features = set(tc["feature_types"]) - ENABLED_FEATURE_TYPES
    if unsupported_features:
        raise ValueError(f"Unsupported feature type: {', '.join(unsupported_features)}")

    if "QUERIES" in tc["feature_types"] and not tc.get("queries"):
        raise ValueError("Missing 'queries' for QUERIES feature type")


def lambda_handler(payload: Payload, context) -> dict:
    try:
        _validate_payload(payload)

        response = _textract_client().analyze_document(**_get_config(payload))

        boto3.client("s3").put_object(
            Bucket=payload["bucket"],
            Key=payload["results_key"],
            Body=json.dumps(response).encode("utf-8"),
        )

        return {"status": "success"}
    except Exception as e:
        print(f"Error processing document: {e}")
        return {"status": "error", "error_reason": str(e)}


def _get_config(payload: Payload) -> dict:
    tc = payload["textract_config"]

    config: dict = {
        "Document": {"S3Object": {"Bucket": payload["bucket"], "Name": payload["key"]}},
        "FeatureTypes": tc["feature_types"],
    }

    if "QUERIES" in tc["feature_types"]:
        config["QueriesConfig"] = {
            "Queries": [
                {"Text": v, "Alias": k} for k, v in (tc.get("queries") or {}).items()
            ]
        }
    return config
