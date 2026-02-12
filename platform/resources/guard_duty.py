"""Guard Duty malware scan config for S3 bucket"""

import pulumi
import pulumi_aws as aws

from utils.config import ACCOUNT_ID
from utils.utils import create_policy_doc

from components import Role, Bucket


def malware_scan_policy(bucket_arn: pulumi.Output[str]) -> pulumi.Output[str]:
    return pulumi.Output.all(acc_id=ACCOUNT_ID, bucket_arn=bucket_arn).apply(
        lambda args: create_policy_doc(
            {
                "Sid": "AllowManagedRuleToSendS3EventsToGuardDuty",
                "Effect": "Allow",
                "Action": ["events:PutRule"],
                "Resource": [
                    f"arn:aws:events:eu-west-2:{args['acc_id']}:rule/DO-NOT-DELETE-AmazonGuardDutyMalwareProtectionS3*"
                ],
                "Condition": {
                    "StringEquals": {
                        "events:ManagedBy": "malware-protection-plan.guardduty.amazonaws.com"
                    },
                    "ForAllValues:StringEquals": {
                        "events:source": "aws.s3",
                        "events:detail-type": [
                            "Object Created",
                            "AWS API Call via CloudTrail",
                        ],
                    },
                    "Null": {"events:source": "false", "events:detail-type": "false"},
                },
            },
            {
                "Sid": "AllowUpdateTargetAndDeleteManagedRule",
                "Effect": "Allow",
                "Action": [
                    "events:DeleteRule",
                    "events:PutTargets",
                    "events:RemoveTargets",
                ],
                "Resource": [
                    f"arn:aws:events:eu-west-2:{args['acc_id']}:rule/DO-NOT-DELETE-AmazonGuardDutyMalwareProtectionS3*"
                ],
                "Condition": {
                    "StringEquals": {
                        "events:ManagedBy": "malware-protection-plan.guardduty.amazonaws.com"
                    }
                },
            },
            {
                "Sid": "AllowGuardDutyToMonitorEventBridgeManagedRule",
                "Effect": "Allow",
                "Action": ["events:DescribeRule", "events:ListTargetsByRule"],
                "Resource": [
                    f"arn:aws:events:eu-west-2:{args['acc_id']}:rule/DO-NOT-DELETE-AmazonGuardDutyMalwareProtectionS3*"
                ],
            },
            {
                "Sid": "AllowEnableS3EventBridgeEvents",
                "Effect": "Allow",
                "Action": ["s3:PutBucketNotification", "s3:GetBucketNotification"],
                "Resource": [args["bucket_arn"]],
                "Condition": {"StringEquals": {"aws:ResourceAccount": args["acc_id"]}},
            },
            {
                "Sid": "AllowPostScanTag",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObjectTagging",
                    "s3:GetObjectVersionTagging",
                    "s3:PutObjectTagging",
                    "s3:PutObjectVersionTagging",
                ],
                "Resource": [f"{args['bucket_arn']}/*"],
                "Condition": {"StringEquals": {"aws:ResourceAccount": args["acc_id"]}},
            },
            {
                "Sid": "AllowPutValidationObject",
                "Effect": "Allow",
                "Action": ["s3:PutObject"],
                "Resource": [
                    f"{args['bucket_arn']}/malware-protection-resource-validation-object"
                ],
                "Condition": {"StringEquals": {"aws:ResourceAccount": args["acc_id"]}},
            },
            {
                "Sid": "AllowCheckBucketOwnership",
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": [args["bucket_arn"]],
                "Condition": {"StringEquals": {"aws:ResourceAccount": args["acc_id"]}},
            },
            {
                "Sid": "AllowMalwareScan",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                "Resource": [f"{args['bucket_arn']}/*"],
                "Condition": {"StringEquals": {"aws:ResourceAccount": args["acc_id"]}},
            },
        )
    )


def malware_scan_role(documents_bucket: Bucket) -> Role:
    return Role(
        "userdb-guard-duty-role",
        assume_role_policy=ACCOUNT_ID.apply(
            lambda acc_id: create_policy_doc(
                {
                    "Sid": "GuardDutyMalwareProtectionForS3",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "malware-protection-plan.guardduty.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {"aws:SourceAccount": acc_id},
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:guardduty:eu-west-2:{acc_id}:malware-protection-plan/*"
                        },
                    },
                }
            )
        ),
        inline_policies=[
            aws.iam.RoleInlinePolicyArgs(
                name="guard-duty-policy",
                policy=malware_scan_policy(documents_bucket.arn),
            )
        ],
    )


def create_malware_scan_rule(documents_bucket: Bucket):
    malware_role = malware_scan_role(documents_bucket)

    aws.guardduty.MalwareProtectionPlan(
        "documents-malware-plan",
        role=malware_role.arn,
        protected_resource=aws.guardduty.MalwareProtectionPlanProtectedResourceArgs(
            s3_bucket=aws.guardduty.MalwareProtectionPlanProtectedResourceS3BucketArgs(
                bucket_name=documents_bucket.name,
                object_prefixes=["uploads/raw/"],
            )
        ),
        actions=[
            aws.guardduty.MalwareProtectionPlanActionArgs(
                taggings=[
                    aws.guardduty.MalwareProtectionPlanActionTaggingArgs(
                        status="ENABLED",
                    )
                ]
            )
        ],
    )
