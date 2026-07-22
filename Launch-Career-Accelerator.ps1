$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $repo "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$log = Join-Path $logDir "career-accelerator-startup.log"
$statusPath = Join-Path $logDir "career-accelerator-bootstrap-status.json"
$readyPath = Join-Path $logDir "career-accelerator-bootstrap-ready.txt"
$splashScript = Join-Path $repo "Show-Career-Accelerator-Bootstrap.ps1"

function Write-StartupLog {
    param([string]$Message)

    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $log -Value "[$stamp] $Message"
}

function Write-BootstrapStatus {
    param(
        [int]$Percent,
        [int]$Step,
        [string]$Message,
        [string]$Detail,
        [string]$State = "running"
    )

    $payload = [ordered]@{
        percent = $Percent
        step = $Step
        total_steps = 8
        message = $Message
        detail = $Detail
        state = $State
    }

    $temporary = $statusPath + ".tmp"
    $payload | ConvertTo-Json -Compress | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $statusPath -Force
}

function Invoke-NativeLogged {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        & $FilePath @Arguments >> $log 2>&1
        $exitCode = [int]$LASTEXITCODE
    }
    catch {
        Write-StartupLog "Native command failed to start: $($_.Exception.Message)"
        $exitCode = 1
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    return $exitCode
}

function Test-RequiredModules {
    param([string]$PythonPath)

    $arguments = @(
        "-c",
        "import PySide6, yaml, duckdb, ipykernel, sql"
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"

    try {
        & $PythonPath @arguments > $null 2>&1
        $exitCode = [int]$LASTEXITCODE
    }
    catch {
        $exitCode = 1
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    return ($exitCode -eq 0)
}

function Start-BootstrapSplash {
    if (-not (Test-Path -LiteralPath $splashScript)) {
        throw "Show-Career-Accelerator-Bootstrap.ps1 was not found."
    }

    Remove-Item -LiteralPath $readyPath -Force -ErrorAction SilentlyContinue

    Write-BootstrapStatus -Percent 4 -Step 1 -Message "Preparing Career Accelerator" -Detail "Opening the startup screen."

    $argumentLine = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -RepositoryPath "{1}" -StatusPath "{2}" -ReadyPath "{3}"' -f $splashScript, $repo, $statusPath, $readyPath

    $process = Start-Process -FilePath "powershell.exe" -ArgumentList $argumentLine -WindowStyle Hidden -PassThru

    for ($attempt = 0; $attempt -lt 80; $attempt++) {
        if (Test-Path -LiteralPath $readyPath) {
            return $process
        }

        if ($process.HasExited) {
            throw "The startup splash could not be opened."
        }

        Start-Sleep -Milliseconds 100
        $process.Refresh()
    }

    throw "The startup splash did not become ready."
}

function Wait-ForApplicationStartup {
    param([System.Diagnostics.Process]$ApplicationProcess)

    for ($attempt = 0; $attempt -lt 1800; $attempt++) {
        Start-Sleep -Milliseconds 100
        $ApplicationProcess.Refresh()

        if ($ApplicationProcess.HasExited) {
            $currentState = ""

            try {
                if (Test-Path -LiteralPath $statusPath) {
                    $statusPayload = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
                    $currentState = [string]$statusPayload.state
                }
            }
            catch {
            }

            if ($currentState -eq "close") {
                return $true
            }

            throw "Career Accelerator exited before startup completed."
        }

        try {
            if (Test-Path -LiteralPath $statusPath) {
                $statusPayload = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json

                if ([string]$statusPayload.state -eq "close") {
                    return $true
                }
            }
        }
        catch {
        }
    }

    Write-StartupLog "The application remained active, but the startup handoff timed out."
    Write-BootstrapStatus -Percent 100 -Step 8 -Message "Startup continuing" -Detail "Career Accelerator is still loading in the background." -State "close"
    return $false
}

$splashProcess = $null

try {
    Set-Location -LiteralPath $repo
    Write-StartupLog "Hidden launcher started."

    $splashProcess = Start-BootstrapSplash
    Write-BootstrapStatus -Percent 8 -Step 1 -Message "Checking application environment" -Detail "Looking for the local Python environment."

    $venv = Join-Path $repo ".venv"
    $python = Join-Path $venv "Scripts\python.exe"
    $pythonw = Join-Path $venv "Scripts\pythonw.exe"
    $requirements = Join-Path $repo "requirements.txt"
    $application = Join-Path $repo "application\app.py"

    if (-not (Test-Path -LiteralPath $python)) {
        Write-StartupLog ".venv is missing. Creating it now."
        Write-BootstrapStatus -Percent 16 -Step 2 -Message "Creating local Python environment" -Detail "First-launch setup is creating the isolated .venv folder. This may take a minute."

        $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue

        if ($null -ne $pyLauncher) {
            $createExitCode = Invoke-NativeLogged -FilePath $pyLauncher.Source -Arguments @(
                "-3",
                "-m",
                "venv",
                $venv
            )
        }
        else {
            $systemPython = Get-Command python.exe -ErrorAction Stop
            $createExitCode = Invoke-NativeLogged -FilePath $systemPython.Source -Arguments @(
                "-m",
                "venv",
                $venv
            )
        }

        if ($createExitCode -ne 0) {
            throw "Could not create .venv. Review the startup log."
        }

        Write-BootstrapStatus -Percent 36 -Step 2 -Message "Local environment created" -Detail "The new .venv folder is ready."
    }

    if (-not (Test-Path -LiteralPath $python)) {
        throw ".venv creation finished, but Scripts\python.exe is missing."
    }

    Write-BootstrapStatus -Percent 42 -Step 3 -Message "Checking application requirements" -Detail "Verifying the packages Career Accelerator needs."

    if (-not (Test-RequiredModules -PythonPath $python)) {
        Write-StartupLog "Installing requirements.txt into .venv."
        Write-BootstrapStatus -Percent 48 -Step 3 -Message "Installing application requirements" -Detail "Downloading and configuring the required Python packages. The first launch can take several minutes."

        if (-not (Test-Path -LiteralPath $requirements)) {
            throw "requirements.txt was not found."
        }

        $installExitCode = Invoke-NativeLogged -FilePath $python -Arguments @(
            "-m",
            "pip",
            "install",
            "-r",
            $requirements,
            "--disable-pip-version-check"
        )

        if ($installExitCode -ne 0) {
            throw "Could not install requirements.txt. Review the startup log."
        }
    }

    Write-BootstrapStatus -Percent 80 -Step 4 -Message "Verifying setup" -Detail "Confirming that the application environment is complete."

    if (-not (Test-RequiredModules -PythonPath $python)) {
        throw "The required application modules are still unavailable."
    }

    if (-not (Test-Path -LiteralPath $pythonw)) {
        throw ".venv\Scripts\pythonw.exe is missing."
    }

    if (-not (Test-Path -LiteralPath $application)) {
        throw "application\app.py was not found."
    }

    Write-StartupLog "Launching Career Accelerator with the existing bootstrap splash."
    Write-BootstrapStatus -Percent 56 -Step 4 -Message "Starting Career Accelerator" -Detail "Importing the application and handing startup progress to the same splash window."

    $previousExternalSplash = $env:CAREER_ACCELERATOR_EXTERNAL_SPLASH
    $previousStatusPath = $env:CAREER_ACCELERATOR_SPLASH_STATUS_PATH

    try {
        $env:CAREER_ACCELERATOR_EXTERNAL_SPLASH = "1"
        $env:CAREER_ACCELERATOR_SPLASH_STATUS_PATH = $statusPath

        $applicationProcess = Start-Process -FilePath $pythonw -ArgumentList @(
            $application
        ) -WorkingDirectory $repo -PassThru
    }
    finally {
        $env:CAREER_ACCELERATOR_EXTERNAL_SPLASH = $previousExternalSplash
        $env:CAREER_ACCELERATOR_SPLASH_STATUS_PATH = $previousStatusPath
    }

    Wait-ForApplicationStartup -ApplicationProcess $applicationProcess | Out-Null
}
catch {
    $message = $_.Exception.Message
    Write-StartupLog "ERROR: $message"

    try {
        Write-BootstrapStatus -Percent 100 -Step 8 -Message "Startup failed" -Detail $message -State "error"
        Start-Sleep -Milliseconds 900
    }
    catch {
    }

    Add-Type -AssemblyName PresentationFramework

    $dialogText = "Career Accelerator could not start.`n`n$message`n`nLog: $log"

    [System.Windows.MessageBox]::Show(
        $dialogText,
        "Career Accelerator Startup Error",
        "OK",
        "Error"
    ) | Out-Null

    try {
        Write-BootstrapStatus -Percent 100 -Step 8 -Message "Startup failed" -Detail $message -State "close"
    }
    catch {
    }

    exit 1
}
finally {
    Start-Sleep -Milliseconds 250
    Remove-Item -LiteralPath $readyPath -Force -ErrorAction SilentlyContinue
}
