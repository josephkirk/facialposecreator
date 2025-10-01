# PowerShell script to run facial_pose_animator unit tests with mayapy
# 
# Usage:
#   .\run_tests.ps1                    - Run all tests  
#   .\run_tests.ps1 TestClassName      - Run specific test class
#   .\run_tests.ps1 -Integration       - Run integration tests
#   .\run_tests.ps1 -NoMaya            - Run mock tests only

param(
    [string]$TestClass = "",
    [switch]$Integration,
    [switch]$NoMaya,
    [switch]$Verbose
)

Write-Host "Facial Pose Animator - Test Runner (PowerShell)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host

# Define potential Maya installation locations
$MayaLocations = @(
    "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe",
    "C:\Program Files\Autodesk\Maya2023\bin\mayapy.exe", 
    "C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe",
    "C:\Program Files\Autodesk\Maya2025\bin\mayapy.exe",
    "C:\Program Files\Autodesk\Maya2021\bin\mayapy.exe"
)

# Find mayapy.exe
$MayaPyPath = $null
foreach ($location in $MayaLocations) {
    if (Test-Path $location) {
        $MayaPyPath = $location
        break
    }
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TestRunnerScript = Join-Path $ScriptDir "run_tests_with_mayapy.py"

# Build arguments
$Arguments = @()

if ($TestClass) {
    $Arguments += $TestClass
}

if ($Integration) {
    $Arguments += "--integration"
}

if ($NoMaya) {
    $Arguments += "--no-maya"
}

if ($Verbose) {
    $Arguments += "--verbose"
}

# Execute tests
if ($MayaPyPath -and (Test-Path $MayaPyPath) -and -not $NoMaya) {
    Write-Host "Found mayapy.exe at: $MayaPyPath" -ForegroundColor Green
    Write-Host "Running tests with Maya environment..." -ForegroundColor Yellow
    Write-Host
    
    try {
        $ProcessArgs = @($TestRunnerScript) + $Arguments
        $Process = Start-Process -FilePath $MayaPyPath -ArgumentList $ProcessArgs -NoNewWindow -Wait -PassThru
        $ExitCode = $Process.ExitCode
        
        Write-Host
        if ($ExitCode -eq 0) {
            Write-Host "Test execution completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Test execution failed with exit code: $ExitCode" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "Error running tests with mayapy: $_" -ForegroundColor Red
        $ExitCode = 1
    }
    
} else {
    if (-not $NoMaya) {
        Write-Host "WARNING: Could not find mayapy.exe in standard Maya installation locations." -ForegroundColor Yellow
        Write-Host "Falling back to regular Python with mock mode..." -ForegroundColor Yellow
    } else {
        Write-Host "Running tests with regular Python (mock mode only)..." -ForegroundColor Yellow
    }
    
    Write-Host
    
    # Add --no-maya to arguments if not already present
    if ($Arguments -notcontains "--no-maya") {
        $Arguments += "--no-maya"
    }
    
    try {
        $ProcessArgs = @($TestRunnerScript) + $Arguments
        $Process = Start-Process -FilePath "python" -ArgumentList $ProcessArgs -NoNewWindow -Wait -PassThru
        $ExitCode = $Process.ExitCode
        
        Write-Host
        if ($ExitCode -eq 0) {
            Write-Host "Test execution completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Test execution failed with exit code: $ExitCode" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "Error running tests with Python: $_" -ForegroundColor Red
        Write-Host
        Write-Host "Make sure Python is installed and available in PATH, or run manually with:" -ForegroundColor Yellow
        Write-Host "  python `"$TestRunnerScript`" --no-maya" -ForegroundColor Cyan
        $ExitCode = 1
    }
}

Write-Host
Write-Host "Test runner finished." -ForegroundColor Cyan

# Return exit code
exit $ExitCode