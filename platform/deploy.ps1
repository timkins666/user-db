#!/usr/bin/env pwsh
# Quick deployment script for Pulumi infrastructure

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "User-DB Platform Deployment" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Pulumi
try {
    $pulumiVersion = pulumi version
    Write-Host "✓ Pulumi: $pulumiVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Pulumi not found. Please install Pulumi CLI" -ForegroundColor Red
    Write-Host "  Install from: https://www.pulumi.com/docs/get-started/install/" -ForegroundColor Yellow
    exit 1
}

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✓ AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ AWS CLI not found (optional but recommended)" -ForegroundColor Yellow
}

Write-Host ""

# Step 1: Install Pulumi dependencies
Write-Host "Step 1: Installing Pulumi dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""

# Step 2: Build Lambda packages
Write-Host "Step 2: Building Lambda packages..." -ForegroundColor Cyan

Write-Host "  Building object_check_lambda..." -ForegroundColor Yellow
Push-Location object_check_lambda
& .\package.ps1
Pop-Location

Write-Host "  Textract runner doesn't need building (uses AWS-provided boto3)" -ForegroundColor Yellow

Write-Host ""

# Step 3: Check Pulumi login
Write-Host "Step 3: Checking Pulumi login status..." -ForegroundColor Cyan
try {
    pulumi whoami | Out-Null
    Write-Host "✓ Already logged in to Pulumi" -ForegroundColor Green
} catch {
    Write-Host "Not logged in to Pulumi. Logging in..." -ForegroundColor Yellow
    pulumi login
}

Write-Host ""

# Step 4: Initialize or select stack
Write-Host "Step 4: Stack configuration..." -ForegroundColor Cyan
$stacks = pulumi stack ls --json 2>&1 | ConvertFrom-Json

if ($stacks -and ($stacks | Where-Object { $_.name -eq "dev" })) {
    Write-Host "Stack 'dev' exists. Selecting it..." -ForegroundColor Yellow
    pulumi stack select dev
} else {
    Write-Host "Creating new stack 'dev'..." -ForegroundColor Yellow
    pulumi stack init dev

    Write-Host "Configuring stack..." -ForegroundColor Yellow
    pulumi config set aws:region eu-west-2
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Ready to deploy!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Preview changes:" -ForegroundColor Yellow
Write-Host "  pulumi preview" -ForegroundColor White
Write-Host ""
Write-Host "Deploy infrastructure:" -ForegroundColor Yellow
Write-Host "  pulumi up" -ForegroundColor White
Write-Host ""

# Optional: Preview
$preview = Read-Host "Would you like to preview the deployment? (y/N)"
if ($preview -eq "y" -or $preview -eq "Y") {
    pulumi preview
    Write-Host ""
}

# Optional: Deploy
$deploy = Read-Host "Would you like to deploy now? (y/N)"
if ($deploy -eq "y" -or $deploy -eq "Y") {
    pulumi up --yes

    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Stack outputs:" -ForegroundColor Yellow
    pulumi stack output
} else {
    Write-Host ""
    Write-Host "Deployment skipped. Run 'pulumi up' when ready." -ForegroundColor Yellow
}
