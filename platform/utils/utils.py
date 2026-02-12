import json
from typing import Any

import pulumi


def create_policy_doc(
    *statements: pulumi.Input[str | dict[str, Any]] | str | dict[str, Any],
) -> pulumi.Output[str]:
    """
    Create an IAM policy document from one or more statements.

    Args:
        *statements: Policy statements as dicts or JSON strings, can be Pulumi Outputs

    Returns:
        A Pulumi Output containing the full policy document as a JSON string
    """
    return pulumi.Output.all(*statements).apply(
        lambda resolved_statements: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    json.loads(s) if isinstance(s, str) else s
                    for s in resolved_statements
                ],
            }
        )
    )
