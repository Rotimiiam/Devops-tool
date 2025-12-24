# Bitbucket Repository Variables Setup Script (PowerShell)
# Run this on your Windows machine to add repository variables

# Configuration
$WORKSPACE = "curaceldev"
$REPO_SLUG = "devops-tool"
$BITBUCKET_USERNAME = "rotimio"

Write-Host "=== Bitbucket Repository Variables Setup ===" -ForegroundColor Cyan
Write-Host ""

# Get App Password
Write-Host "You need a Bitbucket App Password with 'repository:write' scope" -ForegroundColor Yellow
Write-Host "Create one at: https://bitbucket.org/account/settings/app-passwords/" -ForegroundColor Yellow
Write-Host ""
$BITBUCKET_APP_PASSWORD = Read-Host "Enter your Bitbucket App Password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($BITBUCKET_APP_PASSWORD)
$APP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# API endpoint
$API_URL = "https://api.bitbucket.org/2.0/repositories/$WORKSPACE/$REPO_SLUG/pipelines_config/variables"

# Create credentials
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${BITBUCKET_USERNAME}:${APP_PASSWORD}"))

# Function to add a variable
function Add-BitbucketVariable {
    param(
        [string]$Key,
        [string]$Value,
        [bool]$Secured = $false
    )
    
    Write-Host "Adding variable: $Key" -ForegroundColor Green
    
    $body = @{
        key = $Key
        value = $Value
        secured = $Secured
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $API_URL -Method Post `
            -Headers @{
                Authorization = "Basic $base64AuthInfo"
                "Content-Type" = "application/json"
            } `
            -Body $body
        
        Write-Host "✓ Successfully added $Key" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to add $Key" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
    
    Write-Host ""
}

# Get EC2_HOST
Write-Host "Enter your EC2_HOST (e.g., ec2-54-123-45-67.compute-1.amazonaws.com or IP address):"
$EC2_HOST = Read-Host
Add-BitbucketVariable -Key "EC2_HOST" -Value $EC2_HOST -Secured $false

# Get EC2_USER
Write-Host "Enter your EC2_USER (e.g., ubuntu or ec2-user):"
$EC2_USER = Read-Host
Add-BitbucketVariable -Key "EC2_USER" -Value $EC2_USER -Secured $false

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Verify at: https://bitbucket.org/$WORKSPACE/$REPO_SLUG/admin/addon/admin/pipelines/repository-variables" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Docker and Docker Compose on your EC2 instance" -ForegroundColor White
Write-Host "2. Push to main branch to trigger deployment" -ForegroundColor White
