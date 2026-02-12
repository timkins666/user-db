"""AWS step functions state machine component"""

from collections.abc import Callable
import pulumi
import pulumi_aws as aws


from ._base import AwsComponent


class StateMachine(AwsComponent):
    def __init__(
        self,
        name: str,
        definition_fn: Callable,
        role_arn: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
        templates: dict[str, pulumi.Input[str]] | None = None,
    ):
        super().__init__("userdb:infra:stateMachine", name, opts)

        definition = pulumi.Output.all(
            **(templates or {}),
        ).apply(lambda args: definition_fn(**args))

        self.state_machine = aws.sfn.StateMachine(
            name,
            definition=definition,
            role_arn=role_arn,
            opts=pulumi.ResourceOptions.merge(
                opts,
                pulumi.ResourceOptions(parent=self),
            ),
        )

        self.register_outputs(
            {
                "name": self.state_machine.name,
                "arn": self.state_machine.arn,
            }
        )

    @property
    def arn(self) -> pulumi.Output[str]:
        """The ARN of the state machine."""
        return self.state_machine.arn

    @property
    def name(self) -> pulumi.Output[str]:
        """The name of the state machine."""
        return self.state_machine.name
