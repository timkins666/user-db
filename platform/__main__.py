"""
Pulumi infrastructure for user-db document processing platform.
Deploys Lambda functions and Step Function for document validation and Textract processing.
"""

import json
from pathlib import Path
import pulumi
import pulumi_aws as aws

from components import bucket, lambda_, sfn, iam
from utils.config import CONFIG
from utils.utils import create_policy_doc

from process_document_sfn.definition import process_document_definition

PLATFORM_ROOT = Path(__file__).resolve().parent


# Create S3 bucket for document storage
documents_bucket = bucket.Bucket(name=CONFIG.get("bucketName", ""))


# ============================================================================
# Object Check Lambda
# ============================================================================

object_check_role = iam.Role(
    "userdb-object-check-lambda-role",
    assume_role_policy=create_policy_doc(
        {
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Effect": "Allow",
        }
    ),
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="object-check-lambda-policy",
            policy=documents_bucket.arn.apply(
                lambda bucket_arn: create_policy_doc(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListBucket",
                            "s3:GetObject",
                            "s3:GetObjectTagging",
                            "s3:DeleteObject",
                        ],
                        "Resource": [
                            f"{bucket_arn}/uploads/raw/*",
                            bucket_arn,
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["s3:PutObject", "s3:PutObjectTagging"],
                        "Resource": f"{bucket_arn}/uploads/clean/*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": "logs:CreateLogGroup",
                        "Resource": "arn:aws:logs:eu-west-2:145485528601:*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                        "Resource": [
                            "arn:aws:logs:eu-west-2:145485528601:log-group:/aws/lambda/userdb-object-checker:*"
                        ],
                    },
                ),
            ),
        )
    ],
)

object_check_lambda = lambda_.Lambda(
    name="userdb-object-check",
    role=object_check_role.arn,
    runtime="python3.11",
    handler="lambda_function.lambda_handler",
    code=pulumi.FileArchive("./object_check_lambda/lambda-deployment.zip"),
    timeout=30,
    memory_size=256,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "BUCKET_NAME": documents_bucket.name,
        },
    ),
)

# ============================================================================
# Textract Runner Lambda
# ============================================================================

textract_runner_role = iam.Role(
    "userdb-textract-runner-lambda-role",
    assume_role_policy=create_policy_doc(
        {
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Effect": "Allow",
        }
    ),
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="textract-runner-lambda-policy",
            policy=documents_bucket.arn.apply(
                lambda bucket_arn: create_policy_doc(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "textract:AnalyzeDocument",
                        ],
                        "Resource": "*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                        ],
                        "Resource": f"{bucket_arn}/uploads/clean/*",
                    },
                )
            ),
        )
    ],
)

textract_runner_lambda = lambda_.Lambda(
    name="userdb-textract-runner",
    role=textract_runner_role.arn,
    runtime="python3.11",
    handler="lambda_function.lambda_handler",
    code=pulumi.FileArchive("./textract_runner/app"),
    timeout=20,
    memory_size=256,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "BUCKET_NAME": documents_bucket.name,
        },
    ),
)

# ============================================================================
# Step Function
# ============================================================================

# IAM Role for Step Function
sfn_role = iam.Role(
    "userdb-process-document-sfn-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "states.amazonaws.com"},
                    "Effect": "Allow",
                }
            ],
        }
    ),
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="sfn-policy",
            policy=pulumi.Output.all(
                object_check_lambda.arn, textract_runner_lambda.arn
            ).apply(
                lambda lambda_arns: create_policy_doc(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "lambda:InvokeFunction",
                        ],
                        "Resource": lambda_arns,
                    }
                )
            ),
        )
    ],
)


process_document_sfn = sfn.StateMachine(
    name="userdb-process-document",
    role_arn=sfn_role.arn,
    definition_fn=process_document_definition,
    templates={
        "object_check_lambda_arn": object_check_lambda.arn,
        "textract_runner_lambda_arn": textract_runner_lambda.arn,
    },
)

# ============================================================================
# Exports
# ============================================================================

pulumi.export("bucket_name", documents_bucket.name)
pulumi.export("bucket_arn", documents_bucket.arn)
pulumi.export("object_check_lambda_arn", object_check_lambda.arn)
pulumi.export("object_check_lambda_name", object_check_lambda.name)
pulumi.export("textract_runner_lambda_arn", textract_runner_lambda.arn)
pulumi.export("textract_runner_lambda_name", textract_runner_lambda.name)
pulumi.export("step_function_arn", process_document_sfn.arn)
pulumi.export("step_function_name", process_document_sfn.name)
