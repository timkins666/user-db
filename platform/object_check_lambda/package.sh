#!/usr/bin/env bash

# Package Lambda function with dependencies into a deployment zip

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/package"
ZIP_FILE="$SCRIPT_DIR/lambda-deployment.zip"

echo "Cleaning previous package..."
rm -rf "$PACKAGE_DIR"
rm -f "$ZIP_FILE"

echo "Creating package directory..."
mkdir -p "$PACKAGE_DIR"

echo "Installing dependencies to package directory..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" --target "$PACKAGE_DIR" --no-deps --upgrade

echo "Copying Lambda handler code..."
cp -r "$SCRIPT_DIR/app/"* "$PACKAGE_DIR/"

echo "Creating deployment zip..."
cd "$PACKAGE_DIR"
zip -r "$ZIP_FILE" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

cd "$SCRIPT_DIR"
echo ""
echo "✅ Lambda package created: $ZIP_FILE"
echo "Size: $(du -h "$ZIP_FILE" | cut -f1)"
echo ""

if [ "${1:-}" != "-d" ]; then
    echo "Package ready for deployment. Run with -d flag to deploy to AWS."
    exit 0
fi

echo "Deploying..."
aws lambda update-function-code --function-name userdb-object-checker --zip-file "fileb://$ZIP_FILE"
