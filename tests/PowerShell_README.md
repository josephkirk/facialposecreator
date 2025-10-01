# Facial Pose Animator - PowerShell Automation Suite

This suite provides comprehensive PowerShell automation for running containerized Maya tests with Podman or Docker.

## 🚀 Quick Start

```powershell
# Run all tests (simplest usage)
.\run_container_tests.ps1

# Run specific test class with verbose output
.\run_container_tests.ps1 -TestClass TestPoseManagement -Verbose

# Force rebuild and run all tests
.\run_container_tests.ps1 -Rebuild -Force

# Use GUI launcher
.\test_launcher_gui.ps1
```

## 📁 File Structure

```
FacialPoseTools/
├── run_container_tests.ps1     # Main PowerShell automation script
├── run_container_tests.bat     # Batch wrapper for PowerShell script
├── test_launcher_gui.ps1       # Windows Forms GUI launcher
├── container_config.ps1        # Configuration file
├── PowerShell_README.md        # This documentation
└── [Docker files...]
```

## 🛠️ Components

### 1. Main Automation Script (`run_container_tests.ps1`)

The primary automation script handles the complete testing workflow:

**Features:**
- ✅ Automated container engine detection (Podman/Docker)
- ✅ Smart image building and caching
- ✅ Flexible test execution (all tests or specific classes)
- ✅ Comprehensive logging and error handling
- ✅ Result export and management
- ✅ Container cleanup and resource management
- ✅ Colored console output with progress indicators
- ✅ Configuration file support

**Usage:**
```powershell
.\run_container_tests.ps1 [OPTIONS]

# Examples:
.\run_container_tests.ps1                                    # Run all tests
.\run_container_tests.ps1 -TestClass TestFacialPoseData     # Run specific test
.\run_container_tests.ps1 -Rebuild -Verbose                 # Rebuild with verbose output
.\run_container_tests.ps1 -Verify                           # Only verify Maya environment
.\run_container_tests.ps1 -CleanUp -Force                   # Run tests and clean up
.\run_container_tests.ps1 -ContainerEngine docker           # Use Docker instead of Podman
.\run_container_tests.ps1 -OutputDir "my_results"           # Custom output directory
```

### 2. Batch Wrapper (`run_container_tests.bat`)

For users who prefer batch files or need to call from legacy systems:

```cmd
run_container_tests.bat [OPTIONS]

REM Examples:
run_container_tests.bat --help
run_container_tests.bat -v -r
run_container_tests.bat -t TestPoseManagement --verbose
run_container_tests.bat --verify
run_container_tests.bat --docker
```

**Batch Options:**
- `-h, --help` → Show help
- `-v, --verbose` → Enable verbose output
- `-r, --rebuild` → Force rebuild
- `-t, --test <class>` → Run specific test class
- `-o, --output <dir>` → Set output directory
- `--verify` → Verify Maya environment only
- `--cleanup` → Clean up after tests
- `--force` → Skip confirmations
- `--docker` → Use Docker instead of Podman

### 3. GUI Launcher (`test_launcher_gui.ps1`)

A Windows Forms GUI for non-command-line users:

**Features:**
- 🖱️ Point-and-click interface
- 📋 Dropdown test class selection
- ⚙️ Visual configuration options
- 📊 Progress indication
- 📁 One-click results access
- ❓ Built-in help system

**To Launch:**
```powershell
.\test_launcher_gui.ps1
```

### 4. Configuration File (`container_config.ps1`)

Customize default behavior without modifying scripts:

```powershell
# Example configuration
$Config = @{
    ContainerEngine = "podman"          # Default: podman
    ImageName = "facial-pose-tests"     # Default image name
    OutputDir = "test_results"          # Default output directory
    DefaultVerbose = $false             # Default verbosity
    AutoBuild = $true                   # Auto-build missing images
    CleanOldResults = $true             # Clean old results
    ResultRetentionDays = 7             # Keep results for 7 days
    UseColors = $true                   # Colored console output
    
    Performance = @{
        MemoryLimit = "4g"              # Container memory limit
        CpuLimit = "2"                  # Container CPU limit
        ParallelTests = $false          # Parallel execution
    }
    
    Notifications = @{
        ShowDesktop = $false            # Desktop notifications
        PlaySound = $false              # Sound notifications
    }
}
```

## 🎯 Usage Examples

### Development Workflow
```powershell
# Quick development cycle
.\run_container_tests.ps1 -TestClass TestNewFeature -Verbose

# Full validation before commit
.\run_container_tests.ps1 -Rebuild -CleanUp -Force

# CI/CD simulation
.\run_container_tests.ps1 -ContainerEngine docker -OutputDir "ci_results"
```

### Debugging and Troubleshooting
```powershell
# Verify Maya environment
.\run_container_tests.ps1 -Verify -Verbose

# Debug specific test with full output
.\run_container_tests.ps1 -TestClass TestFailingTest -Verbose -Force

# Clean slate rebuild
.\run_container_tests.ps1 -Rebuild -CleanUp -Force -Verbose
```

### Batch Operations
```powershell
# Test multiple classes sequentially
"TestFacialPoseData", "TestPoseManagement", "TestFileOperations" | ForEach-Object {
    .\run_container_tests.ps1 -TestClass $_ -OutputDir "results_$_"
}

# Performance comparison across container engines
@("podman", "docker") | ForEach-Object {
    Measure-Command { .\run_container_tests.ps1 -ContainerEngine $_ -OutputDir "perf_$_" }
}
```

## 📊 Output and Results

### Console Output
The scripts provide rich console output with:
- 🔵 **Info messages** (Cyan)
- ✅ **Success messages** (Green)  
- ⚠️ **Warning messages** (Yellow)
- ❌ **Error messages** (Red)
- 🔄 **Step indicators** (Magenta)

### Result Files
Results are saved to the specified output directory:

```
test_results/
├── automation.log          # Detailed automation log
├── test_results.txt        # Test execution summary
├── test.log               # Container test log
└── [additional files...]
```

### Exit Codes
- `0` - Success
- `1` - Container engine not found
- `2` - Build failed
- `3` - Tests failed
- `4` - Maya verification failed
- `99` - Unhandled exception

## ⚙️ Configuration Options

### Environment Variables
Set these before running scripts to customize behavior:

```powershell
$env:CONTAINER_ENGINE = "docker"        # Override default container engine
$env:FACIAL_POSE_VERBOSE = "true"       # Enable verbose by default
$env:FACIAL_POSE_AUTO_CLEANUP = "true"  # Enable automatic cleanup
```

### PowerShell Execution Policy
If you get execution policy errors:

```powershell
# For current session only
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# For current user (permanent)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run script with bypass (one-time)
powershell -ExecutionPolicy Bypass -File .\run_container_tests.ps1
```

## 🔧 Troubleshooting

### Common Issues

1. **PowerShell Execution Policy**
   ```powershell
   # Error: "execution of scripts is disabled on this system"
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Container Engine Not Found**
   ```powershell
   # Install Podman
   winget install RedHat.Podman
   
   # Or install Docker
   winget install Docker.DockerDesktop
   ```

3. **Permission Errors**
   ```powershell
   # Run PowerShell as Administrator, or use:
   .\run_container_tests.ps1 -Force
   ```

4. **Container Build Failures**
   ```powershell
   # Check connectivity and try rebuilding
   .\run_container_tests.ps1 -Rebuild -Verbose
   ```

5. **GUI Won't Start**
   ```powershell
   # Ensure .NET Framework is available
   Add-Type -AssemblyName System.Windows.Forms
   
   # Try from PowerShell ISE or VS Code
   ```

### Debugging Steps

1. **Check prerequisites:**
   ```powershell
   # Verify PowerShell version (requires 5.1+)
   $PSVersionTable.PSVersion
   
   # Check container engine
   podman --version  # or docker --version
   
   # Verify script location
   Get-Location
   ```

2. **Enable verbose logging:**
   ```powershell
   .\run_container_tests.ps1 -Verbose
   ```

3. **Check log files:**
   ```powershell
   Get-Content .\test_results\automation.log -Tail 50
   ```

4. **Manual container verification:**
   ```powershell
   # Build manually
   podman build -t facial-pose-tests .
   
   # Test manually
   podman run --rm facial-pose-tests --verify
   ```

## 🚀 Performance Tips

1. **Use cached images:** Don't use `-Rebuild` unless necessary
2. **Specific test classes:** Run only what you need during development
3. **Parallel execution:** Consider running different test classes in parallel manually
4. **Resource limits:** Configure memory/CPU limits in `container_config.ps1`
5. **SSD storage:** Use SSD for Docker/Podman storage for faster container operations

## 🔗 Integration

### VS Code Integration
Add to VS Code tasks.json:
```json
{
    "label": "Run Maya Container Tests",
    "type": "shell",
    "command": "powershell",
    "args": ["-File", ".\\run_container_tests.ps1"],
    "group": "test",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
    }
}
```

### GitHub Actions
```yaml
- name: Run Maya Tests
  shell: pwsh
  run: .\run_container_tests.ps1 -ContainerEngine docker -Force
```

### Scheduled Tasks
```powershell
# Create scheduled task for nightly tests
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Path\To\run_container_tests.ps1 -CleanUp -Force"
$trigger = New-ScheduledTaskTrigger -Daily -At 2AM
Register-ScheduledTask -TaskName "FacialPoseTests" -Action $action -Trigger $trigger
```

## 📚 Advanced Usage

### Custom Test Runners
Create custom test configurations:

```powershell
# custom_test_suite.ps1
param([string]$Environment = "dev")

$testConfig = @{
    "dev" = @("TestFacialPoseData", "TestControlSelection")
    "staging" = @("TestPoseManagement", "TestFileOperations") 
    "prod" = @("TestRealMayaOperations", "TestUndoTracking")
}

$testConfig[$Environment] | ForEach-Object {
    Write-Host "Running $_ for $Environment environment"
    .\run_container_tests.ps1 -TestClass $_ -OutputDir "results_${Environment}_$_"
}
```

### Performance Monitoring
```powershell
# Monitor test performance over time
$results = @()
1..5 | ForEach-Object {
    $time = Measure-Command { .\run_container_tests.ps1 -Force }
    $results += [PSCustomObject]@{ Run = $_; Duration = $time.TotalSeconds }
}
$results | Export-Csv "performance_results.csv"
```

This PowerShell automation suite provides a complete, professional-grade testing solution for the Facial Pose Animator Maya plugin!