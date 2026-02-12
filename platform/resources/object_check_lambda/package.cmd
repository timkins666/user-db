@echo off
REM Package Lambda function with dependencies for deployment

setlocal

set SCRIPT_DIR=%~dp0
set PACKAGE_DIR=%SCRIPT_DIR%package
set ZIP_FILE=%SCRIPT_DIR%lambda-deployment.zip

echo Cleaning previous package...
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"

echo Creating package directory...
mkdir "%PACKAGE_DIR%"

echo Installing dependencies to package directory...
pip install -r "%SCRIPT_DIR%requirements.txt" --target "%PACKAGE_DIR%" --no-deps --upgrade

echo Copying Lambda handler code...
xcopy "%SCRIPT_DIR%app\*" "%PACKAGE_DIR%\" /E /I /Y

echo.
echo Creating deployment zip...
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%PACKAGE_DIR%', '%ZIP_FILE%')"

echo.
echo ✅ Lambda package created: %ZIP_FILE%
echo.
echo Ready for Pulumi deployment!
