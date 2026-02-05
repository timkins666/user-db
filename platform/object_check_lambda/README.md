# Object Check Lambda

Lambda function to validate uploaded files for security and compliance.

## Features

- File type signature validation using the `filetype` Python package (inspects file headers, not extensions)
- Checks GuardDuty malware scan status via the S3 object tag `GuardDutyMalwareScanStatus` (expects `NO_THREATS_FOUND`)
- Allowed types: PDF, JPG/JPEG, PNG

## Dependencies

Install Python dependencies listed in `requirements.txt` into your virtualenv or use the included `package.sh` to create a deployment bundle.

```bash
pip install -r requirements.txt
```

`requirements.txt` currently includes:

- `filetype` - detect file signatures

## How it works

1. The Lambda receives a payload with `bucket` and `key`.
2. It checks the S3 object tags for `GuardDutyMalwareScanStatus` and waits briefly for the tag to appear (up to a timeout). The object is only accepted if the tag value is `NO_THREATS_FOUND`.
3. It fetches the first ~8 KB of the object and uses `filetype` to detect the MIME type from the file header.
4. The function accepts the file only if the detected MIME type is one of `application/pdf`, `image/jpeg`, or `image/png`.

## Packaging for Lambda (.zip)

Use the provided `package.sh` script to build and deploy ZIP containing the handler and dependencies:

```bash
cd platform/object_check_lambda
./package.sh
```

## Payload Format

```json
{
  "bucket": "your-bucket-name",
  "key": "path/to/file.pdf"
}
```

## Response Format

### Success

```json
{
  "file_ok": true
}
```

### Failure (examples)

```json
{ "file_ok": false, "reason": "missing bucket or key" }
{ "file_ok": false, "reason": "virus_detected_or_scan_failed" }
{ "file_ok": false, "reason": "invalid_file_type" }
```

## IAM Permissions

The function needs permission to read and put S3 objects and tags, and delete objects.

## Local Testing

Quick test using a local Python environment (with `boto3` and `moto` for mocked S3):

```bash
pip install -r requirements.txt
pytest -q
```
