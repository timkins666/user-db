"""
Lambda handler to validate uploaded files:
- Checks GuardDuty malware scan status via S3 object tags
- Checks file type signature (magic bytes) to ensure it's PDF, JPG, or PNG
"""

import json
import time
import urllib.parse
import boto3
import botocore.exceptions
import filetype

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


s3 = None  # lazy init s3 client


def lambda_handler(payload, context):
    print("Received payload: " + json.dumps(payload, indent=2))

    bucket = payload["bucket"]
    key = urllib.parse.unquote_plus(payload["key"], encoding="utf-8")

    if not bucket or not key:
        print("Invalid payload: missing bucket or key")
        return {"file_ok": False, "reason": "missing bucket or key"}

    if not _file_exists(bucket, key):
        print(f"File s3://{bucket}/{key} does not exist")
        return {"file_ok": False, "reason": "file_not_found"}

    if not _check_guard_duty_malware_tag(bucket, key):
        return {
            "file_ok": False,
            "reason": "virus_detected_or_scan_failed",
        }

    if not _check_file_type(bucket, key):
        return {
            "file_ok": False,
            "reason": "invalid_file_type",
        }

    new_key = _move_to_clean_prefix(bucket, key)

    return {"file_ok": True, "new_key": new_key}


def _s3_client():
    global s3

    if s3 is None:
        s3 = boto3.client("s3")

    return s3


def _file_exists(bucket, key) -> bool:
    try:
        _s3_client().head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError:
        return False


def _check_file_type(bucket, key) -> bool:
    try:
        resp = _s3_client().get_object(
            Bucket=bucket,
            Key=key,
            Range=f"bytes=0-{8092 - 1}",
        )
        head = resp["Body"].read()

        kind = filetype.guess(head)
        if not kind:
            print("Unknown file type")
            return False

        if kind.mime not in ALLOWED_MIME_TYPES:
            print(f"Disallowed type: {kind.mime}")
            return False

        return True
    except Exception as e:
        print(f"Error checking file signature: {e}")
        return False


def _check_guard_duty_malware_tag(bucket, key) -> bool:
    max_wait = 60  # seconds
    malware_status = None
    try:
        while max_wait > -1:
            tagging = _s3_client().get_object_tagging(Bucket=bucket, Key=key)
            malware_status = next(
                (
                    t["Value"]
                    for t in tagging["TagSet"]
                    if t["Key"] == "GuardDutyMalwareScanStatus"
                ),
                None,
            )

            if malware_status:
                break

            max_wait -= 5
            time.sleep(5)

        print(f"GuardDutyMalwareScanStatus: {malware_status}")
        return malware_status == "NO_THREATS_FOUND"
    except Exception as e:
        print(f"Error checking GuardDuty malware tag: {e}")
        return False


def _move_to_clean_prefix(bucket: str, key: str) -> str:
    """Move object from uploads/raw/... to uploads/clean/... retaining tags.

    Returns the new key on success.
    """
    s3 = _s3_client()

    raw_prefix = "uploads/raw/"
    clean_prefix = "uploads/clean/"

    dest_key = clean_prefix + key[len(raw_prefix) :]

    copy_source = {"Bucket": bucket, "Key": key}

    print(f"Copying s3://{bucket}/{key} to s3://{bucket}/{dest_key}")

    # Use TaggingDirective='COPY' to preserve tags from source
    s3.copy_object(
        CopySource=copy_source, Bucket=bucket, Key=dest_key, TaggingDirective="COPY"
    )

    # Delete the source object
    s3.delete_object(Bucket=bucket, Key=key)

    print(f"Moved object to s3://{bucket}/{dest_key}")
    return dest_key


# not used, keeping for reference
# CLAMD_SOCKET = "/run/clamav/clamd.sock"
# def _scan_file(tmp_file_path, cd) -> bool:
#     try:
#         scan_result = cd.scan_file(tmp_file_path)
#         print(f"ClamAV scan result: {scan_result}")

#         if scan_result:
#             print(f"Virus detected: {scan_result}")
#             return False

#         print("File passed all checks")
#         return True

#     except Exception as e:
#         print("Error in antivirus scanning: " + str(e))
#         return False


# def _get_clamd():
#     global _clamd

#     if _clamd is not None:
#         return _clamd

#     print("Starting clamd")

#     try:
#         import pyclamd

#         subprocess.Popen(["/usr/sbin/clamd", "-c", "/etc/clamd.d/clamd.conf"])

#         # Wait until socket exists and clamd responds, up to 10 mins
#         start = time.perf_counter()
#         for i in range(600):
#             if os.path.exists(CLAMD_SOCKET):
#                 cd = pyclamd.ClamdUnixSocket(CLAMD_SOCKET)
#                 if cd.ping():
#                     _clamd = cd
#                     break

#             if i and i % 30 == 0:
#                 print(f"Still waiting for clamd to start... {i} seconds elapsed")
#             time.sleep(1)

#         if i == 599:
#             print("clamd did not start in 10 minutes :(")
#             return None

#         print(
#             "clamd eventually started in %d seconds", int(time.perf_counter() - start)
#         )
#         return _clamd

#     except Exception as e:
#         print("Failed to initialize ClamAV: " + str(e))
#         return None
