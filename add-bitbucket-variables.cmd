@echo off
REM Bitbucket Repository Variables Setup Script (Windows CMD)
REM This uses curl which is available in Windows 10+

setlocal enabledelayedexpansion

REM Configuration
set WORKSPACE=curaceldev
set REPO_SLUG=devops-tool
set BITBUCKET_USERNAME=rotimio

echo === Bitbucket Repository Variables Setup ===
echo.

echo You need a Bitbucket App Password with 'repository:write' scope
echo Create one at: https://bitbucket.org/account/settings/app-passwords/
echo.

set /p BITBUCKET_APP_PASSWORD="Enter your Bitbucket App Password: "
echo.

REM API endpoint
set API_URL=https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables

REM Get EC2_HOST
set /p EC2_HOST="Enter your EC2_HOST (e.g., ec2-54-123-45-67.compute-1.amazonaws.com): "
echo Adding variable: EC2_HOST
curl -X POST -u "%BITBUCKET_USERNAME%:%BITBUCKET_APP_PASSWORD%" ^
    -H "Content-Type: application/json" ^
    -d "{\"key\": \"EC2_HOST\", \"value\": \"%EC2_HOST%\", \"secured\": false}" ^
    "%API_URL%"
echo.
echo.

REM Get EC2_USER
set /p EC2_USER="Enter your EC2_USER (e.g., ubuntu or ec2-user): "
echo Adding variable: EC2_USER
curl -X POST -u "%BITBUCKET_USERNAME%:%BITBUCKET_APP_PASSWORD%" ^
    -H "Content-Type: application/json" ^
    -d "{\"key\": \"EC2_USER\", \"value\": \"%EC2_USER%\", \"secured\": false}" ^
    "%API_URL%"
echo.
echo.

echo === Setup Complete ===
echo Verify at: https://bitbucket.org/%WORKSPACE%/%REPO_SLUG%/admin/addon/admin/pipelines/repository-variables
echo.
echo Next steps:
echo 1. Install Docker and Docker Compose on your EC2 instance
echo 2. Push to main branch to trigger deployment
echo.

pause
