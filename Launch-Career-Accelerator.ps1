$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $repo "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log = Join-Path $logDir "career-accelerator-startup.log"

function Write-StartupLog([string]$Message) {
    Add-Content -Path $log -Value ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message)
}

try {
    Set-Location $repo
    Write-StartupLog "Hidden launcher started."

    $python = Join-Path $repo ".venv\Scripts\python.exe"
    $pythonw = Join-Path $repo ".venv\Scripts\pythonw.exe"

    if (-not (Test-Path $python)) {
        $systemPython = (Get-Command python.exe -ErrorAction Stop).Source
        Write-StartupLog "Creating virtual environment."
        & $systemPython -m venv (Join-Path $repo ".venv") *> $log
        if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
    }

    Write-StartupLog "Checking requirements."
    & $python -c "import PySide6" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-StartupLog "Installing application requirements."
        & $python -m pip install -r (Join-Path $repo "requirements.txt") --disable-pip-version-check *> $log
        if ($LASTEXITCODE -ne 0) { throw "Application requirements could not be installed." }
    }

    if (-not (Test-Path $pythonw)) {
        throw "pythonw.exe was not found in the local environment."
    }

    Write-StartupLog "Launching Career Accelerator."
    Start-Process -FilePath $pythonw -ArgumentList @((Join-Path $repo "application\app.py")) -WorkingDirectory $repo
}
catch {
    Write-StartupLog ("ERROR: " + $_.Exception.Message)
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "Career Accelerator could not start.`n`n$($_.Exception.Message)`n`nLog: $log",
        "Career Accelerator Startup Error",
        "OK",
        "Error"
    ) | Out-Null
    exit 1
}
