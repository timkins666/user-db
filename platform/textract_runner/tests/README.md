# Textract Runner Tests

Unit tests for the Textract Runner Lambda function using moto to mock AWS services.

## Setup

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

Run specific test:

```bash
pytest tests/test_lambda_function.py::test_lambda_handler_success -v
```

## Test Coverage

The test suite covers:

- ✅ Successful document processing with Textract
- ✅ Storing Textract results in S3
- ✅ Missing required payload fields (bucket, key, results_key)
- ✅ Empty and None payload values
- ✅ Multiple document processing
- ✅ Nested S3 paths

## Mocked Services

- **S3**: Document storage and results retrieval
- **Textract**: Document analysis API
