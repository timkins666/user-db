"""AWS Lambda function component"""

import pulumi
import pulumi_aws as aws

from ._base import AwsComponent


class Lambda(AwsComponent):
    def __init__(
        self,
        name,
        role: pulumi.Input[str],
        runtime: str,
        handler: str,
        code: pulumi.Input[pulumi.asset.Archive],
        timeout: int,
        memory_size: int,
        environment: aws.lambda_.FunctionEnvironmentArgs | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):

        super().__init__("userdb:infra:lambda", name, opts)

        self.function = aws.lambda_.Function(
            name,
            role=role,
            runtime=runtime,
            handler=handler,
            code=code,
            timeout=timeout,
            memory_size=memory_size,
            environment=environment,
            opts=pulumi.ResourceOptions.merge(
                opts,
                pulumi.ResourceOptions(parent=self),
            ),
        )

        self.register_outputs(
            {
                "name": self.function.id,
                "arn": self.function.arn,
            }
        )

    @property
    def arn(self) -> pulumi.Output[str]:
        """The ARN of the Lambda function."""
        return self.function.arn

    @property
    def name(self) -> pulumi.Output[str]:
        """The name of the Lambda function."""
        return self.function.name
