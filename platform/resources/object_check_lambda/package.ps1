#!/usr/bin/env pwsh
# Package Lambda function with dependencies for deployment (PowerShell version)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageDir = Join-Path $ScriptDir "package"
$ZipFile = Join-Path $ScriptDir "lambda-deployment.zip"

Write-Host "Cleaning previous package..." -ForegroundColor Yellow
if (Test-Path $PackageDir) {
    Remove-Item -Recurse -Force $PackageDir
}
if (Test-Path $ZipFile) {
    Remove-Item -Force $ZipFile
}

Write-Host "Creating package directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $PackageDir | Out-Null

Write-Host "Installing dependencies to package directory..." -ForegroundColor Yellow
pip install -r (Join-Path $ScriptDir "requirements.txt") --target $PackageDir --no-deps --upgrade

Write-Host "Copying Lambda handler code..." -ForegroundColor Yellow
$AppDir = Join-Path $ScriptDir "app"
Copy-Item -Path "$AppDir\*" -Destination $PackageDir -Recurse -Force

Write-Host ""
Write-Host "✅ Lambda package created in: $PackageDir" -ForegroundColor Green
Write-Host ""
Write-Host "Ready for Pulumi deployment!" -ForegroundColor Cyan
