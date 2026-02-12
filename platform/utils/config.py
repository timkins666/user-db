# pulumi config stuff

import pulumi
import pulumi_aws as aws

CONFIG = pulumi.Config("userdb")
AWS_CONFIG = pulumi.Config("aws")

REGION = AWS_CONFIG.require("region")
ACCOUNT_ID = aws.get_caller_identity_output().account_id

DEFAULT_TAGS = {
    "App": "userdb",
    "Environment": pulumi.get_stack(),
    "Project": "userdb",
    "ManagedBy": "Pulumi",
}
