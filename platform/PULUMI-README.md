# User-DB Platform Infrastructure

Pulumi infrastructure-as-code for deploying userdb resources to AWS.

## Architecture

- **S3 Bucket**: Stores uploaded documents and Textract results
- **Object Check Lambda**: Validates document security and file types
- **Textract Runner Lambda**: Runs AWS Textract analysis on documents
- **Step Function**: Orchestrates the document processing workflow

## Prerequisites

1. **Python 3.11+**
2. **Pulumi CLI**: [Install Pulumi](https://www.pulumi.com/docs/get-started/install/)
3. **AWS CLI**: Configured with appropriate credentials

## Building Lambda Packages

### Object Check Lambda

The object check lambda has external dependencies that need to be packaged:

```bash
cd object_check_lambda
bash package.sh
```

This creates a zip with all dependencies ready for deployment.

### Textract Runner Lambda

No build step needed - uses only boto3 which is provided by AWS Lambda runtime.

## Deployment

### Initialize Pulumi

First time setup:

```bash
pulumi login s3://<state-bucket-and-path>
pulumi stack init dev
```

### Configure Stack

Set required configuration:

```bash
pulumi config set aws:region eu-west-2

# Set custom bucket name
pulumi config set bucketName my-documents-bucket
```

### Deploy

Preview changes:

```bash
pulumi preview
```

Deploy to AWS:

```bash
pulumi up
```

### View Outputs

After deployment, view the created resources:

```bash
pulumi stack output
```

Example output:

```text
bucket_name                user-db-documents-dev
object_check_lambda_arn    arn:aws:lambda:eu-west-2:...
textract_runner_lambda_arn arn:aws:lambda:eu-west-2:...
step_function_arn          arn:aws:states:eu-west-2:...
```

## Testing the Deployment


### Upload a Test Document

```bash
aws s3 cp test-document.pdf s3://$(pulumi stack output bucket_name --show-secrets)/uploads/raw/test-document.pdf
```

### Invoke Step Function

```bash
aws stepfunctions start-execution \
  --state-machine-arn $(pulumi stack output step_function_arn --show-secrets) \
  --input "{\"bucket\": \"$(pulumi stack output bucket_name --show-secrets)\", \"key\": \"uploads/raw/test-document.pdf\", \"textract_config\": {\"feature_types\":[\"FORMS\"]} }"
```

## Updating Infrastructure

After making changes to `__main__.py`:

```bash
pulumi up
```

## Destroying Resources

To tear down all resources:

```bash
pulumi destroy
```

## Stack Management

### Multiple Environments

Create separate stacks for different environments:

```bash
# Create production stack
pulumi stack init prod
pulumi config set aws:region eu-west-2
pulumi config set bucketName prod-documents

# Switch between stacks
pulumi stack select dev
pulumi stack select prod
```

### View Stack Resources

```bash
pulumi stack
```

## Lambda Updates

### Update Object Check Lambda

After making code changes:

```bash
cd object_check_lambda
bash package.sh
cd ..
pulumi up
```

### Update Textract Runner Lambda

```bash
pulumi up
```

Pulumi will detect changes and update the Lambda function automatically.

## Troubleshooting

### Lambda Logs

View CloudWatch logs:

```bash
aws logs tail /aws/lambda/userdb-object-checker --follow
aws logs tail /aws/lambda/userdb-textract-runner --follow
```

### Step Function Execution

View execution history:

```bash
aws stepfunctions list-executions \
  --state-machine-arn $(pulumi stack output step_function_arn --show-secrets)
```

## Security

- S3 bucket has public access blocked
- GuardDuty malware protection currently manually enabled for S3, and is required for the object check to succeed
