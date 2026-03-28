# Load environment variables from .env file
# Usage: . .\load-env.ps1

$envFile = Join-Path $PSScriptRoot ".env"

if (-Not (Test-Path $envFile)) {
    Write-Host "Error: .env file not found at $envFile"
    exit 1
}

Write-Host "Loading environment variables from .env..."

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    
    # Skip empty lines and comments
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }
    
    # Parse KEY=VALUE
    if ($line -match "^([^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        
        # Set environment variable for current session
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

Write-Host "Environment variables loaded successfully!"
