# pulumi config stuff

import pulumi

CONFIG = pulumi.Config("userdb")
AWS_CONFIG = pulumi.Config("aws")
REGION = AWS_CONFIG.require("region")
