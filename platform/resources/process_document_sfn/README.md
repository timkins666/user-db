# Basic state function to run textract

This is entirely unnecessary and could be a single lambda, but that's not the point.

Calls check object lambda, then textract on the object once moved to the clean location.

## Prod like improvements that I'm omitting, assuming it did stay as a sfn

- Lambda runner for textract/dump to S3 due to limited sfn payload
- Async textract job & polling
- Conditional retries depending on fail
- Check textract reponse pagination
