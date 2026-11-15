@echo off
rem Builds Gorsche as a Windows GUI binary (no console window).
setlocal

cd /d "%~dp0"

go build -ldflags "-H=windowsgui" -o gorsche.exe .
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Built gorsche.exe
endlocal
