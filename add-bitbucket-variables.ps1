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

Write-Host "=== EC2 Configuration ===" -ForegroundColor Cyan
# Get EC2_HOST
Write-Host "Enter your EC2_HOST (e.g., ec2-54-123-45-67.compute-1.amazonaws.com or IP address):"
$EC2_HOST = Read-Host
Add-BitbucketVariable -Key "EC2_HOST" -Value $EC2_HOST -Secured $false

# Get EC2_USER
Write-Host "Enter your EC2_USER (e.g., ubuntu or ec2-user):"
$EC2_USER = Read-Host
Add-BitbucketVariable -Key "EC2_USER" -Value $EC2_USER -Secured $false

Write-Host ""
Write-Host "=== OAuth Credentials ===" -ForegroundColor Cyan
# Bitbucket OAuth
Write-Host "Enter your BITBUCKET_CLIENT_ID:"
$BITBUCKET_CLIENT_ID = Read-Host
Add-BitbucketVariable -Key "BITBUCKET_CLIENT_ID" -Value $BITBUCKET_CLIENT_ID -Secured $false

Write-Host "Enter your BITBUCKET_CLIENT_SECRET:"
$BITBUCKET_CLIENT_SECRET = Read-Host
Add-BitbucketVariable -Key "BITBUCKET_CLIENT_SECRET" -Value $BITBUCKET_CLIENT_SECRET -Secured $true

# GitHub OAuth
Write-Host "Enter your GITHUB_CLIENT_ID:"
$GITHUB_CLIENT_ID = Read-Host
Add-BitbucketVariable -Key "GITHUB_CLIENT_ID" -Value $GITHUB_CLIENT_ID -Secured $false

Write-Host "Enter your GITHUB_CLIENT_SECRET:"
$GITHUB_CLIENT_SECRET = Read-Host
Add-BitbucketVariable -Key "GITHUB_CLIENT_SECRET" -Value $GITHUB_CLIENT_SECRET -Secured $true

Write-Host ""
Write-Host "=== API Keys ===" -ForegroundColor Cyan
# Gemini API Key
Write-Host "Enter your GEMINI_API_KEY:"
$GEMINI_API_KEY = Read-Host
Add-BitbucketVariable -Key "GEMINI_API_KEY" -Value $GEMINI_API_KEY -Secured $true

Write-Host ""
Write-Host "=== Application Secrets ===" -ForegroundColor Cyan
# Secret Key
Write-Host "Enter your SECRET_KEY (or press Enter to generate a random one):"
$SECRET_KEY = Read-Host
if ([string]::IsNullOrWhiteSpace($SECRET_KEY)) {
    $SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    Write-Host "Generated SECRET_KEY: $SECRET_KEY" -ForegroundColor Yellow
}
Add-BitbucketVariable -Key "SECRET_KEY" -Value $SECRET_KEY -Secured $true

# Database Password
Write-Host "Enter your POSTGRES_PASSWORD (or press Enter to generate a random one):"
$POSTGRES_PASSWORD = Read-Host
if ([string]::IsNullOrWhiteSpace($POSTGRES_PASSWORD)) {
    $POSTGRES_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    Write-Host "Generated POSTGRES_PASSWORD: $POSTGRES_PASSWORD" -ForegroundColor Yellow
}
Add-BitbucketVariable -Key "POSTGRES_PASSWORD" -Value $POSTGRES_PASSWORD -Secured $true

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Verify at: https://bitbucket.org/$WORKSPACE/$REPO_SLUG/admin/addon/admin/pipelines/repository-variables" -ForegroundColor Yellow
Write-Host ""
Write-Host "Variables added:" -ForegroundColor Cyan
Write-Host "  - EC2_HOST" -ForegroundColor White
Write-Host "  - EC2_USER" -ForegroundColor White
Write-Host "  - BITBUCKET_CLIENT_ID" -ForegroundColor White
Write-Host "  - BITBUCKET_CLIENT_SECRET (secured)" -ForegroundColor White
Write-Host "  - GITHUB_CLIENT_ID" -ForegroundColor White
Write-Host "  - GITHUB_CLIENT_SECRET (secured)" -ForegroundColor White
Write-Host "  - GEMINI_API_KEY (secured)" -ForegroundColor White
Write-Host "  - SECRET_KEY (secured)" -ForegroundColor White
Write-Host "  - POSTGRES_PASSWORD (secured)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Verify SSH keys are configured in Bitbucket" -ForegroundColor White
Write-Host "2. Push to main branch to trigger deployment" -ForegroundColor White
Write-Host "3. Access your app at http://launchpad.crl.to" -ForegroundColor White
