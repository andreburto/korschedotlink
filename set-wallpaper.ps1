param(
    [Parameter(Mandatory=$false)]
    [string]$ImagePath
)

<#
.SYNOPSIS
    Sets the desktop wallpaper to the specified image.

.DESCRIPTION
    This script takes an image path and sets it as the Windows desktop wallpaper.
    If no image path is provided, it generates a new portrait using portrait_maker.py.

.PARAMETER ImagePath
    The full path to the image file to set as wallpaper. If not provided, a new image will be generated.

.EXAMPLE
    .\set-wallpaper.ps1 -ImagePath "C:\images\wallpaper.jpg"

.EXAMPLE
    .\set-wallpaper.ps1
#>

# If no image path provided, generate one
if ([string]::IsNullOrEmpty($ImagePath)) {
    Write-Host "No image path provided. Generating new portrait..." -ForegroundColor Cyan
    
    $PythonExe = "C:/Program Files/Python311/python.exe"
    $ScriptPath = Join-Path $PSScriptRoot "src\portrait_maker.py"
    
    # Run the portrait maker and capture the output (last line is the image path)
    $Output = & $PythonExe $ScriptPath 2>&1
    
    # Display all output except the last line
    $OutputLines = $Output -split "`n"
    for ($i = 0; $i -lt ($OutputLines.Count - 1); $i++) {
        Write-Host $OutputLines[$i]
    }
    
    # The last line should be the image path
    $ImagePath = $OutputLines[-1].Trim()
    
    Write-Host "`nGenerated image: $ImagePath" -ForegroundColor Green
}

# Check if the file exists
if (-not (Test-Path $ImagePath)) {
    Write-Error "Image file not found: $ImagePath"
    exit 1
}

# Get the absolute path
$AbsolutePath = (Resolve-Path $ImagePath).Path

Write-Host "Setting wallpaper to: $AbsolutePath"

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
    [Wallpaper]::SetWallpaper($AbsolutePath)
    Write-Host "Wallpaper set successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to set wallpaper: $_"
    exit 1
}
