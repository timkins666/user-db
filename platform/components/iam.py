"""AWS IAM components"""

import json
import pulumi
import pulumi_aws as aws

from ._base import AwsComponent


class Role(AwsComponent):
    def __init__(
        self,
        name,
        assume_role_policy: pulumi.Input[str | dict],
        inline_policies: list[aws.iam.RoleInlinePolicyArgs] | None = None,
        managed_policy_arns: list[pulumi.Input[str]] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("userdb:infra:iamrole", name)

        # Handle dict and Output inputs by converting to JSON string
        assume_role_policy_input = pulumi.Output.from_input(assume_role_policy).apply(
            lambda policy: json.dumps(policy) if isinstance(policy, dict) else policy
        )

        self.role = aws.iam.Role(
            name,
            assume_role_policy=assume_role_policy_input,
            inline_policies=inline_policies,
            managed_policy_arns=managed_policy_arns,
            opts=pulumi.ResourceOptions.merge(
                opts,
                pulumi.ResourceOptions(parent=self),
            ),
        )

    @property
    def arn(self) -> pulumi.Output[str]:
        """The ARN of the IAM role."""
        return self.role.arn

    @property
    def name(self) -> pulumi.Output[str]:
        """The name of the IAM role."""
        return self.role.name
