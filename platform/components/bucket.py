from typing import Optional
import pulumi
import pulumi_aws as aws

from ._base import AwsComponent


class Bucket(AwsComponent):
    def __init__(
        self,
        name: str,
        versioning_enabled: bool = False,
        cors_rules: Optional[list[aws.s3.BucketCorsConfigurationCorsRuleArgs]] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__("userdb:infra:bucket", name)

        self.bucket = aws.s3.Bucket(
            name,
            opts=pulumi.ResourceOptions.merge(
                opts,
                pulumi.ResourceOptions(parent=self),
            ),
            tags=self.tags,
        )

        # Block public access
        self.bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
            f"{name}-public-access-block",
            bucket=self.bucket.id,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True,
            restrict_public_buckets=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        if versioning_enabled:
            self.bucket_versioning = aws.s3.BucketVersioningV2(
                f"{name}-versioning",
                bucket=self.bucket.id,
                versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(
                    status="Enabled",
                ),
                opts=pulumi.ResourceOptions(parent=self),
            )

        if cors_rules:
            self.bucket_cors = aws.s3.BucketCorsConfiguration(
                f"{name}-cors",
                bucket=self.bucket.id,
                cors_rules=cors_rules,
                opts=pulumi.ResourceOptions(parent=self),
            )

        self.register_outputs(
            {
                "arn": self.arn,
                "name": self.name,
            }
        )

    @property
    def arn(self) -> pulumi.Output[str]:
        """The ARN of the S3 bucket."""
        return self.bucket.arn

    @property
    def name(self) -> pulumi.Output[str]:
        """The name of the S3 bucket."""
        return self.bucket.bucket
