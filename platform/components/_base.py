"""AWS provider"""

import pulumi
import pulumi_aws as aws

from utils.config import REGION

aws_provider = aws.Provider(
    "default",
    region=REGION,
    default_tags=aws.ProviderDefaultTagsArgs(
        tags={
            "app": "userdb",
            "Environment": pulumi.get_stack(),
            "Project": "userdb",
            "ManagedBy": "Pulumi",
        }
    ),
)


class AwsComponent(pulumi.ComponentResource):
    def __init__(self, type_, name, opts=None, tags=None):
        self._name = name
        self.tags = {
            "Name": name,
            **(tags or {}),
        }

        opts = pulumi.ResourceOptions.merge(
            pulumi.ResourceOptions(provider=aws_provider),
            opts,
        )
        super().__init__(type_, name, None, opts)
