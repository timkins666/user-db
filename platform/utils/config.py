# pulumi config stuff

import pulumi

CONFIG = pulumi.Config("userdb")
AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")

DEFAULT_TAGS = {
    "App": "userdb",
    "Environment": pulumi.get_stack(),
    "Project": "userdb",
    "ManagedBy": "Pulumi",
}
