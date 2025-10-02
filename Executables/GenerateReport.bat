@echo off
setlocal

:: Path to the PowerShell script (assumed same folder)
set "psScript=%~dp0setup.ps1"

:: Run PowerShell script with bypass execution policy to avoid blocks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%psScript%"

pause
