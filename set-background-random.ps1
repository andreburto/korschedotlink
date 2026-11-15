<#
.SYNOPSIS
    Sets the desktop wallpaper to a random portrait image.

.DESCRIPTION
    This script searches the images directory for portrait_*_resized.jpg files
    and randomly selects one to set as the desktop wallpaper.

.EXAMPLE
    .\set-background-random.ps1
#>

# Get the images directory path
$ImagesDir = Join-Path $PSScriptRoot "images"

# Check if images directory exists
if (-not (Test-Path $ImagesDir)) {
    Write-Error "Images directory not found: $ImagesDir"
    exit 1
}

# Find all portrait resized images
$PortraitImages = Get-ChildItem -Path $ImagesDir -Filter "portrait_*_resized.jpg"

# Check if any images were found
if ($PortraitImages.Count -eq 0) {
    Write-Error "No portrait images found matching pattern: portrait_*_resized.jpg"
    exit 1
}

Write-Host "Found $($PortraitImages.Count) portrait image(s)" -ForegroundColor Cyan

# Randomly select one image
$RandomImage = $PortraitImages | Get-Random
$ImagePath = $RandomImage.FullName

Write-Host "Selected: $($RandomImage.Name)" -ForegroundColor Green
Write-Host "Setting wallpaper to: $ImagePath"

# Define the SystemParametersInfo function from user32.dll
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class Wallpaper {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
    
    public const int SPI_SETDESKWALLPAPER = 0x0014;
    public const int SPIF_UPDATEINIFILE = 0x01;
    public const int SPIF_SENDCHANGE = 0x02;
    
    public static void SetWallpaper(string path) {
        SystemParametersInfo(SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE);
    }
}
"@

try {
    [Wallpaper]::SetWallpaper($ImagePath)
    Write-Host "Wallpaper set successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to set wallpaper: $_"
    exit 1
}
