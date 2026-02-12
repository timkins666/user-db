"""tests for aws/ssm.py"""

import pytest

from userdb.aws import ssm
from tests.conftest import MockParameters


def test_get_parameter_returns_bucket_name():
    """test get_parameter returns the documents bucket name"""

    result = ssm.get_parameter(ssm.Parameter.DOCUMENTS_BUCKET_NAME)
    assert result == MockParameters.documents_bucket_name


def test_get_parameter_returns_step_function_arn():
    """test get_parameter returns the step function ARN"""

    result = ssm.get_parameter(ssm.Parameter.STEP_FUNCTION_ARN)
    assert result == MockParameters.process_document_step_function_arn


def test_get_parameter_with_nonexistent_parameter():
    """test get_parameter raises error for nonexistent parameter"""

    # Clear cache to ensure we actually call SSM
    ssm.get_parameter.cache_clear()

    with pytest.raises(Exception):
        # Create a mock Parameter that doesn't exist in SSM
        ssm.get_parameter("/userdb/nonexistent-parameter")
