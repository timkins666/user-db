"""Tests for aws/sfn.py"""

# pylint: disable=protected-access

import json
from unittest import mock

import pytest

from userdb.aws import sfn
from tests.conftest import MockEnv


class TestProcessDocument:
    """Tests for process_document function"""

    async def test_process_document_success(self):
        """Test process_document successfully processes a document"""
        mock_sfn_client = mock.MagicMock()

        # Simulate execution completing on second check
        mock_sfn_client.describe_execution.side_effect = [
            {"status": "RUNNING"},
            {"status": "SUCCEEDED"},
        ]

        textract_results = {
            "Blocks": [
                {
                    "BlockType": "QUERY",
                    "Id": "query-1",
                    "Query": {"Alias": "firstname"},
                    "Relationships": [{"Type": "ANSWER", "Ids": ["answer-1"]}],
                },
                {
                    "BlockType": "QUERY_RESULT",
                    "Id": "answer-1",
                    "Text": "John",
                },
                {
                    "BlockType": "QUERY",
                    "Id": "query-2",
                    "Query": {"Alias": "lastname"},
                    "Relationships": [{"Type": "ANSWER", "Ids": ["answer-2"]}],
                },
                {
                    "BlockType": "QUERY_RESULT",
                    "Id": "answer-2",
                    "Text": "Smith",
                },
            ]
        }

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
            mock.patch.object(
                sfn.s3,
                sfn.s3.get_object.__name__,
                return_value=json.dumps(textract_results),
            ),
        ):
            result = await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"
            )

        assert result.success is True
        assert result.payload
        assert result.payload.firstname == "John"
        assert result.payload.lastname == "Smith"

        # Verify the correct calls were made
        mock_sfn_client.start_execution.assert_called_once()
        call_args = mock_sfn_client.start_execution.call_args
        assert call_args[1]["stateMachineArn"] == "sf_arn"

        input_payload = json.loads(call_args[1]["input"])
        assert input_payload["bucket"] == "test-bucket"
        assert input_payload["key"] == f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"

    @pytest.mark.asyncio
    async def test_process_document_failed_execution(self):
        """Test process_document returns failure when execution fails"""
        mock_sfn_client = mock.MagicMock()
        mock_sfn_client.describe_execution.return_value = {"status": "FAILED"}

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
        ):
            result = await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"
            )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_process_document_timeout_execution(self):
        """Test process_document handles timeout status"""
        mock_sfn_client = mock.MagicMock()
        mock_sfn_client.describe_execution.return_value = {"status": "TIMED_OUT"}

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
        ):
            result = await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"
            )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_process_document_polls_until_complete(self):
        """Test process_document polls execution status until not RUNNING"""
        mock_sfn_client = mock.MagicMock()

        # Simulate multiple RUNNING states before success
        mock_sfn_client.describe_execution.side_effect = [
            {"status": "RUNNING"},
            {"status": "RUNNING"},
            {"status": "RUNNING"},
            {"status": "SUCCEEDED"},
        ]

        textract_results = {"Blocks": []}

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
            mock.patch.object(
                sfn.s3,
                sfn.s3.get_object.__name__,
                return_value=json.dumps(textract_results),
            ),
        ):
            result = await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"
            )

        # Verify describe_execution was called 4 times
        assert mock_sfn_client.describe_execution.call_count == 4
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_document_constructs_correct_results_key(self):
        """Test process_document constructs the correct S3 key for results"""
        mock_sfn_client = mock.MagicMock()
        mock_sfn_client.describe_execution.return_value = {"status": "SUCCEEDED"}

        textract_results = {"Blocks": []}
        mock_s3_get = mock.MagicMock(return_value=json.dumps(textract_results))

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
            mock.patch.object(sfn.s3, sfn.s3.get_object.__name__, mock_s3_get),
        ):
            await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/document.pdf"
            )

        # Verify the correct results key was constructed
        mock_s3_get.assert_called_once_with(
            bucket="test-bucket",
            key=f"{MockEnv.CLEAN_PATH_PREFIX}/user123/document.pdf-analyzed.json",
        )

    @pytest.mark.asyncio
    async def test_process_document_aborted_execution(self):
        """Test process_document handles aborted status"""
        mock_sfn_client = mock.MagicMock()
        mock_sfn_client.describe_execution.return_value = {"status": "ABORTED"}

        with (
            mock.patch.object(
                sfn, sfn._client.__wrapped__.__name__, return_value=mock_sfn_client
            ),
        ):
            result = await sfn.process_document(
                f"{MockEnv.UPLOAD_PATH_PREFIX}/user123/doc.pdf"
            )

        assert result.success is False
