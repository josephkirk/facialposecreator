# Facial Pose Animator - Automated Podman Testing Script
# Automates the complete container testing workflow
# Usage: .\run_container_tests.ps1 [options]

param(
    [string]$TestClass = "",
    [string]$OutputDir = "test_results",
    [switch]$Rebuild = $false,
    [switch]$Verbose = $false,
    [switch]$Verify = $false,
    [switch]$Help = $false,
    [switch]$CleanUp = $false,
    [switch]$Force = $false,
    [string]$ContainerEngine = "podman"
)

# Load configuration
$ConfigPath = Join-Path $PSScriptRoot "container_config.ps1"
if (Test-Path $ConfigPath) {
    try {
        $Config = & $ConfigPath
        Write-Verbose "Loaded configuration from: $ConfigPath"
    } catch {
        Write-Warning "Failed to load configuration file, using defaults: $_"
        $Config = @{}
    }
} else {
    $Config = @{}
}

# Configuration with defaults
$ImageName = if ($Config.ImageName) { $Config.ImageName } else { "facial-pose-tests" }
$ProjectRoot = $PSScriptRoot
$ResultsDir = Join-Path $ProjectRoot $OutputDir
$LogFile = Join-Path $ResultsDir "automation.log"

# Apply configuration defaults if parameters not specified
if (-not $PSBoundParameters.ContainsKey('ContainerEngine') -and $Config.ContainerEngine) {
    $ContainerEngine = $Config.ContainerEngine
}
if (-not $PSBoundParameters.ContainsKey('Verbose') -and $Config.DefaultVerbose) {
    $Verbose = $Config.DefaultVerbose
}

# Color output functions
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔄 $Message" -ForegroundColor Magenta
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
    
    switch ($Level) {
        "ERROR" { Write-Error $Message }
        "WARN" { Write-Warning $Message }
        "SUCCESS" { Write-Success $Message }
        default { Write-Info $Message }
    }
}

# Help function
function Show-Help {
    Write-Host @"
Facial Pose Animator - Container Testing Automation

USAGE:
    .\run_container_tests.ps1 [OPTIONS]

OPTIONS:
    -TestClass <string>     Run specific test class (e.g., TestFacialPoseData)
    -OutputDir <string>     Output directory for results (default: test_results)
    -Rebuild               Force rebuild of container image
    -Verbose               Enable verbose output
    -Verify                Only verify Maya environment
    -CleanUp               Clean up containers and images after testing
    -Force                 Force operations (skip confirmations)
    -ContainerEngine <string>  Use 'podman' or 'docker' (default: podman)
    -Help                  Show this help message

EXAMPLES:
    # Run all tests with default settings
    .\run_container_tests.ps1

    # Run specific test class with verbose output
    .\run_container_tests.ps1 -TestClass TestPoseManagement -Verbose

    # Force rebuild and run all tests
    .\run_container_tests.ps1 -Rebuild -Force

    # Verify Maya environment only
    .\run_container_tests.ps1 -Verify

    # Run tests with cleanup and custom output directory
    .\run_container_tests.ps1 -OutputDir "my_results" -CleanUp

    # Use Docker instead of Podman
    .\run_container_tests.ps1 -ContainerEngine docker

EXIT CODES:
    0 - Success
    1 - Container engine not found
    2 - Build failed
    3 - Tests failed
    4 - Maya verification failed
"@
}

# Check if container engine is available
function Test-ContainerEngine {
    try {
        $result = & $ContainerEngine --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Container engine '$ContainerEngine' found: $result"
            return $true
        }
    }
    catch {
        # Ignore exception
    }
    
    Write-Log "Container engine '$ContainerEngine' not found or not working" "ERROR"
    Write-Error "Please install $ContainerEngine first:"
    if ($ContainerEngine -eq "podman") {
        Write-Host "  winget install RedHat.Podman"
        Write-Host "  Or download from: https://podman.io/getting-started/installation"
    } else {
        Write-Host "  winget install Docker.DockerDesktop"
        Write-Host "  Or download from: https://www.docker.com/products/docker-desktop/"
    }
    return $false
}

# Check if image exists
function Test-ImageExists {
    try {
        $result = & $ContainerEngine images --format "{{.Repository}}" | Where-Object { $_ -eq $ImageName }
        return $result -eq $ImageName
    }
    catch {
        return $false
    }
}

# Build container image
function Build-ContainerImage {
    Write-Step "Building container image '$ImageName'"
    Write-Log "Starting container image build"
    
    $buildArgs = @("build", "-t", $ImageName)
    if ($Verbose) {
        $buildArgs += "--log-level", "debug"
    }
    $buildArgs += "."
    
    try {
        Push-Location $ProjectRoot
        $output = & $ContainerEngine @buildArgs 2>&1
        $buildSuccess = $LASTEXITCODE -eq 0
        
        if ($buildSuccess) {
            Write-Log "Container image built successfully" "SUCCESS"
            Write-Success "Image '$ImageName' built successfully"
        } else {
            Write-Log "Container image build failed: $output" "ERROR"
            Write-Error "Failed to build container image"
            Write-Host $output
            return $false
        }
    }
    catch {
        Write-Log "Container build exception: $_" "ERROR"
        Write-Error "Build failed with exception: $_"
        return $false
    }
    finally {
        Pop-Location
    }
    
    return $true
}

# Clean old results
function Clear-OldResults {
    if (-not $Config.CleanOldResults -or -not $Config.ResultRetentionDays) {
        return
    }
    
    try {
        $cutoffDate = (Get-Date).AddDays(-$Config.ResultRetentionDays)
        $oldFiles = Get-ChildItem $ResultsDir -File | Where-Object { $_.LastWriteTime -lt $cutoffDate }
        
        if ($oldFiles) {
            Write-Log "Cleaning up $($oldFiles.Count) old result files"
            $oldFiles | Remove-Item -Force
            Write-Info "Cleaned up old results (older than $($Config.ResultRetentionDays) days)"
        }
    }
    catch {
        Write-Log "Failed to clean old results: $_" "WARN"
    }
}

# Run container tests
function Invoke-ContainerTests {
    Write-Step "Running container tests"
    
    # Prepare output directory
    if (-not (Test-Path $ResultsDir)) {
        New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
        Write-Log "Created results directory: $ResultsDir"
    }
    
    # Clean old results if configured
    Clear-OldResults
    
    # Build container arguments
    $runArgs = @("run", "--rm")
    
    # Mount results directory
    $hostPath = (Resolve-Path $ResultsDir).Path
    $runArgs += "-v", "${hostPath}:/app/test_results"
    
    # Add image name
    $runArgs += $ImageName
    
    # Add test-specific arguments
    if ($Verify) {
        $runArgs += "--verify"
    } elseif ($TestClass) {
        $runArgs += $TestClass
    }
    
    if ($Verbose) {
        $runArgs += "--verbose"
    }
    
    Write-Log "Container command: $ContainerEngine $($runArgs -join ' ')"
    Write-Info "Running: $ContainerEngine $($runArgs -join ' ')"
    
    try {
        $output = & $ContainerEngine @runArgs 2>&1
        $testSuccess = $LASTEXITCODE -eq 0
        
        # Display output
        Write-Host $output
        
        if ($testSuccess) {
            Write-Log "Container tests completed successfully" "SUCCESS"
            Write-Success "Tests completed successfully"
            
            # Show results summary if available
            $resultsFile = Join-Path $ResultsDir "test_results.txt"
            if (Test-Path $resultsFile) {
                Write-Step "Test Results Summary"
                $results = Get-Content $resultsFile -Raw
                Write-Host $results
            }
        } else {
            Write-Log "Container tests failed" "ERROR"
            Write-Error "Tests failed or container execution failed"
            return $false
        }
    }
    catch {
        Write-Log "Container execution exception: $_" "ERROR"
        Write-Error "Failed to run container: $_"
        return $false
    }
    
    return $true
}

# Clean up containers and images
function Remove-ContainerArtifacts {
    if (-not $Force) {
        $confirmation = Read-Host "Are you sure you want to clean up containers and images? (y/N)"
        if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
            Write-Info "Cleanup cancelled"
            return
        }
    }
    
    Write-Step "Cleaning up container artifacts"
    
    # Remove stopped containers
    try {
        $containers = & $ContainerEngine ps -a --filter "ancestor=$ImageName" --format "{{.ID}}"
        if ($containers) {
            Write-Info "Removing containers..."
            & $ContainerEngine rm $containers 2>$null
            Write-Log "Removed containers: $($containers -join ', ')"
        }
    }
    catch {
        Write-Log "Failed to remove containers: $_" "WARN"
    }
    
    # Remove image
    try {
        if (Test-ImageExists) {
            Write-Info "Removing image '$ImageName'..."
            & $ContainerEngine rmi $ImageName 2>$null
            Write-Log "Removed image: $ImageName" "SUCCESS"
            Write-Success "Cleaned up image '$ImageName'"
        }
    }
    catch {
        Write-Log "Failed to remove image: $_" "WARN"
        Write-Warning "Could not remove image '$ImageName'"
    }
    
    # Prune unused resources
    try {
        Write-Info "Pruning unused container resources..."
        & $ContainerEngine system prune -f 2>$null
        Write-Log "Container system prune completed"
    }
    catch {
        Write-Log "System prune failed: $_" "WARN"
    }
}

# Main execution function
function Start-AutomatedTesting {
    Write-Host @"
🚀 Facial Pose Animator - Automated Container Testing
============================================================
Container Engine: $ContainerEngine
Project Root: $ProjectRoot
Results Directory: $ResultsDir
Image Name: $ImageName
"@

    # Initialize logging
    if (-not (Test-Path $ResultsDir)) {
        New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
    }
    
    Write-Log "=== Automated Container Testing Started ===" "INFO"
    Write-Log "Parameters: TestClass='$TestClass', Rebuild=$Rebuild, Verify=$Verify, Verbose=$Verbose"
    
    # Step 1: Check container engine
    if (-not (Test-ContainerEngine)) {
        exit 1
    }
    
    # Step 2: Check if rebuild is needed or requested
    $needsBuild = $Rebuild -or -not (Test-ImageExists)
    
    if ($needsBuild) {
        if (-not (Build-ContainerImage)) {
            Write-Log "Build failed, exiting" "ERROR"
            exit 2
        }
    } else {
        Write-Info "Using existing image '$ImageName'"
        Write-Log "Using existing container image"
    }
    
    # Step 3: Run tests
    $testSuccess = Invoke-ContainerTests
    
    # Step 4: Cleanup if requested
    if ($CleanUp) {
        Remove-ContainerArtifacts
    }
    
    # Step 5: Final results
    Write-Step "Automation Complete"
    Write-Log "=== Automated Container Testing Completed ==="
    
    if ($testSuccess) {
        Write-Success "All operations completed successfully!"
        Write-Info "Results available in: $ResultsDir"
        Write-Info "Automation log: $LogFile"
        exit 0
    } else {
        Write-Error "Testing failed!"
        if ($Verify) {
            Write-Log "Maya verification failed" "ERROR"
            exit 4
        } else {
            Write-Log "Container tests failed" "ERROR"
            exit 3
        }
    }
}

# Script entry point
try {
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Validate container engine parameter
    if ($ContainerEngine -notin @("podman", "docker")) {
        Write-Error "Invalid container engine '$ContainerEngine'. Use 'podman' or 'docker'."
        exit 1
    }
    
    Start-AutomatedTesting
}
catch {
    Write-Log "Unhandled exception in automation script: $_" "ERROR"
    Write-Error "Automation failed with exception: $_"
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 99
}