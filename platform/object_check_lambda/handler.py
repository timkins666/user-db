# pylint: skip-file

"""
{
  "bucket": "timmy-userdb",
  "key": "uploads/asa/44297511-792d-4245-8330-b29533d4dd96_testdoc.png"
}
"""

import json
import urllib.parse
import boto3

s3 = boto3.client("s3")


def lambda_handler(payload, context):
    print("Received payload: " + json.dumps(payload, indent=2))

    bucket = payload["bucket"]
    key = urllib.parse.unquote_plus(payload["key"], encoding="utf-8")

    if not bucket or not key:
        print("Invalid payload: missing bucket or key")
        return {"file_ok": False}

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response["ContentType"])
        return {"file_ok": True}
    except Exception:
        return {"file_ok": False}
