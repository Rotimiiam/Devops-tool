# Bitbucket CLI Setup for Repository Variables

## Install Bitbucket CLI

### Windows (PowerShell)
```powershell
# Using Scoop
scoop install bitbucket

# Or download from GitHub releases
# https://github.com/bitbucket-cli/bitbucket-cli/releases
```

### Alternative: Use curl with Bitbucket API directly

Since there isn't an official Bitbucket CLI like GitHub's `gh`, you can use curl commands:

## Setup Authentication

Create an App Password at: https://bitbucket.org/account/settings/app-passwords/

Required scopes:
- `repository:write`
- `pipeline:write`

## Add Repository Variables Using curl

### Windows PowerShell Commands:

```powershell
# Set your credentials
$WORKSPACE = "curaceldev"
$REPO_SLUG = "devops-tool"
$USERNAME = "rotimio"
$APP_PASSWORD = "your-app-password-here"

# Base64 encode credentials
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${USERNAME}:${APP_PASSWORD}"))

# API endpoint
$API_URL = "https://api.bitbucket.org/2.0/repositories/$WORKSPACE/$REPO_SLUG/pipelines_config/variables"

# Function to add a variable
function Add-Variable {
    param($Key, $Value, $Secured = $false)
    
    $body = @{
        key = $Key
        value = $Value
        secured = $Secured
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri $API_URL -Method Post `
        -Headers @{
            Authorization = "Basic $base64Auth"
            "Content-Type" = "application/json"
        } `
        -Body $body
    
    Write-Host "✓ Added $Key"
}

# Add all variables
Add-Variable "EC2_HOST" "your-ec2-host"
Add-Variable "EC2_USER" "ubuntu"
Add-Variable "BITBUCKET_CLIENT_ID" "your-bitbucket-client-id"
Add-Variable "BITBUCKET_CLIENT_SECRET" "your-bitbucket-secret" -Secured $true
Add-Variable "GITHUB_CLIENT_ID" "your-github-client-id"
Add-Variable "GITHUB_CLIENT_SECRET" "your-github-secret" -Secured $true
Add-Variable "GEMINI_API_KEY" "your-gemini-key" -Secured $true
Add-Variable "SECRET_KEY" "your-secret-key" -Secured $true
Add-Variable "POSTGRES_PASSWORD" "your-db-password" -Secured $true
```

### Windows CMD Commands:

```cmd
set WORKSPACE=curaceldev
set REPO_SLUG=devops-tool
set USERNAME=rotimio
set APP_PASSWORD=your-app-password-here

REM Add EC2_HOST
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"EC2_HOST\", \"value\": \"your-ec2-host\", \"secured\": false}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add EC2_USER
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"EC2_USER\", \"value\": \"ubuntu\", \"secured\": false}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add BITBUCKET_CLIENT_ID
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"BITBUCKET_CLIENT_ID\", \"value\": \"your-client-id\", \"secured\": false}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add BITBUCKET_CLIENT_SECRET (secured)
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"BITBUCKET_CLIENT_SECRET\", \"value\": \"your-client-secret\", \"secured\": true}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add GITHUB_CLIENT_ID
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"GITHUB_CLIENT_ID\", \"value\": \"your-github-id\", \"secured\": false}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add GITHUB_CLIENT_SECRET (secured)
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"GITHUB_CLIENT_SECRET\", \"value\": \"your-github-secret\", \"secured\": true}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add GEMINI_API_KEY (secured)
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"GEMINI_API_KEY\", \"value\": \"your-gemini-key\", \"secured\": true}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add SECRET_KEY (secured)
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"SECRET_KEY\", \"value\": \"your-secret-key\", \"secured\": true}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"

REM Add POSTGRES_PASSWORD (secured)
curl -X POST -u "%USERNAME%:%APP_PASSWORD%" ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"POSTGRES_PASSWORD\", \"value\": \"your-db-password\", \"secured\": true}" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"
```

## List Existing Variables

```powershell
# PowerShell
Invoke-RestMethod -Uri $API_URL -Method Get `
    -Headers @{Authorization = "Basic $base64Auth"}
```

```cmd
REM CMD
curl -u "%USERNAME%:%APP_PASSWORD%" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables"
```

## Delete a Variable

```powershell
# PowerShell
$variableUuid = "{variable-uuid-here}"
Invoke-RestMethod -Uri "$API_URL/$variableUuid" -Method Delete `
    -Headers @{Authorization = "Basic $base64Auth"}
```

```cmd
REM CMD
curl -X DELETE -u "%USERNAME%:%APP_PASSWORD%" ^
  "https://api.bitbucket.org/2.0/repositories/%WORKSPACE%/%REPO_SLUG%/pipelines_config/variables/{variable-uuid}"
```

## Quick Setup Script

Just run the PowerShell script we created:

```powershell
.\add-bitbucket-variables.ps1
```

This will interactively prompt you for all values and add them to Bitbucket.

## Verify Variables

After adding, verify at:
https://bitbucket.org/curaceldev/devops-tool/admin/addon/admin/pipelines/repository-variables
