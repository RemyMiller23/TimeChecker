# Get the current script directory (i.e. where the .ps1 file is running from)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set variables
$repoFolder = "TimeChecker"
$downloadUrl = "https://github.com/RemyMiller23/TimeChecker/archive/refs/heads/main.zip"
$zipName = "TimeChecker.zip"
$zipPath = Join-Path $scriptDir $zipName
$repoPath = Join-Path $scriptDir $repoFolder

# Prompt for leave days
do {
    $leaveDays = Read-Host "Enter the total number of days of leave for the month (Public Holidays, Annual Leave & Sick leave)"
    if ($leaveDays -notmatch '^\d+$') {
        Write-Host "Invalid input. Please enter a whole number." -ForegroundColor Red
        $valid = $false
    } else {
        $valid = $true
    }
} while (-not $valid)

# Prompt for reminders
Write-Host "`nEnter any reminders for the next report."
Write-Host "Type each line and press Enter. Submit a blank line to finish.`n"

$reminderLines = @()
while ($true) {
    $line = Read-Host "Reminder >"
    if ([string]::IsNullOrWhiteSpace($line)) { break }
    $reminderLines += $line
}

# Download and unzip if needed
if (-Not (Test-Path $repoPath)) {
    Write-Host "Downloading ZIP to script folder..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

    Write-Host "Unzipping in script folder..." -ForegroundColor Yellow
    Expand-Archive -LiteralPath $zipPath -DestinationPath $scriptDir -Force
    Remove-Item -Path $zipPath -Force

    $extractedFolder = Join-Path $scriptDir "TimeChecker-main"
    if (Test-Path $extractedFolder) {
        Rename-Item -Path $extractedFolder -NewName $repoFolder
        Write-Host "Folder renamed to $repoFolder" -ForegroundColor Green
    } else {
        Write-Host "Folder TimeChecker-main not found!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "$repoFolder already exists. Skipping download and unzip." -ForegroundColor Blue
}

# ✅ Move contents out of TimeChecker to script folder, then delete folder
if (Test-Path $repoPath) {
    Get-ChildItem -Path $repoPath -Force | ForEach-Object {
        $destination = Join-Path $scriptDir $_.Name
        Move-Item -Path $_.FullName -Destination $destination -Force
    }

    Remove-Item -Path $repoPath -Recurse -Force
    Write-Host "Moved contents out of $repoFolder and deleted the folder." -ForegroundColor Green
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Setup virtual environment
$venvPath = Join-Path $scriptDir "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-Not (Test-Path $activateScript)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath

    if (-Not (Test-Path $activateScript)) {
        Write-Host "Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Blue
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
. $activateScript

# Install requirements
$reqFile = Join-Path $scriptDir "requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    pip install --upgrade pip
    pip install -r $reqFile
} else {
    Write-Host "No requirements.txt found." -ForegroundColor Red
}

# Update reminders file
$remindersFile = Join-Path $scriptDir "Reminder.txt"
Set-Content -Path $remindersFile -Value $null
if ($reminderLines.Count -gt 0) {
    foreach ($line in $reminderLines) {
        if ($line.Length -gt 23) {
            $formattedLine = $line.Substring(0, 23) + "`t" + $line.Substring(23)
        } else {
            $formattedLine = $line
        }
        Add-Content -Path $remindersFile -Value $formattedLine
    }
    Write-Host "Reminders saved." -ForegroundColor Green
} else {
    Write-Host "No reminders entered." -ForegroundColor Blue
}

# Update ReportGenerator.py with leave days
$pythonFile = Join-Path $scriptDir "ReportGenerator.py"
(Get-Content $pythonFile) | ForEach-Object {
    if ($_ -match '^\s*generateReport\s*\(\d+\)') {
        "generateReport($leaveDays)"
    } else {
        $_
    }
} | Set-Content $pythonFile

# Run the script
python $pythonFile

# Get current date
$date = Get-Date

# If it's the 1st of the month, go back one month
if ($date.Day -eq 1) {
    $date = $date.AddMonths(-1)
}

# Format: "Month - yyyy"
$reportName = $date.ToString("MMMM - yyyy")

# Show the name
Write-Host "Report name: $reportName" -ForegroundColor Green

# Build full file name (assumes it's in same directory as script)
$reportPath = Join-Path -Path $PSScriptRoot -ChildPath "$reportName.txt"

# Open the file (creates it if it doesn't exist)
if (-not (Test-Path $reportPath)) {
    New-Item -Path $reportPath -ItemType File -Force | Out-Null
}

# Launch the file with default app (Notepad)
Start-Process $reportPath