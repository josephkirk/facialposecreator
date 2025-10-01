# Facial Pose Animator - Container Testing Configuration
# This file contains default settings for the automated testing scripts
# Modify these values to customize the default behavior

# Container Configuration
$Config = @{
    # Default container engine ('podman' or 'docker')
    ContainerEngine = "podman"
    
    # Default image name
    ImageName = "facial-pose-tests"
    
    # Default output directory for test results
    OutputDir = "test_results"
    
    # Auto-rebuild image if it doesn't exist
    AutoBuild = $true
    
    # Default verbosity level
    DefaultVerbose = $false
    
    # Automatically clean up old results before running new tests
    CleanOldResults = $true
    
    # Maximum age of results to keep (in days)
    ResultRetentionDays = 7
    
    # Default timeout for container operations (in seconds)
    ContainerTimeout = 600
    
    # Enable colored output
    UseColors = $true
    
    # Log all operations to file
    EnableLogging = $true
    
    # Automatically open results folder after successful test run
    OpenResultsOnSuccess = $false
    
    # Default test classes to run (empty array means run all)
    DefaultTestClasses = @()
    
    # Maya version to use (affects base image selection)
    MayaVersion = "2024"
    
    # Additional container run arguments
    AdditionalRunArgs = @()
    
    # Performance settings
    Performance = @{
        # Limit container memory usage (e.g., "4g" for 4 gigabytes)
        MemoryLimit = ""
        
        # Limit container CPU usage (e.g., "2" for 2 cores)
        CpuLimit = ""
        
        # Enable parallel test execution if supported
        ParallelTests = $false
    }
    
    # Notification settings
    Notifications = @{
        # Show desktop notifications (Windows 10/11)
        ShowDesktop = $false
        
        # Play sound on completion
        PlaySound = $false
        
        # Send email on test completion (requires SMTP configuration)
        SendEmail = $false
        
        # Email configuration (only used if SendEmail is true)
        EmailConfig = @{
            SmtpServer = ""
            Port = 587
            UseSSL = $true
            From = ""
            To = @()
            Subject = "Facial Pose Animator Test Results"
        }
    }
    
    # Development settings
    Development = @{
        # Keep container running after tests for debugging
        KeepContainerRunning = $false
        
        # Mount source code as volume for live editing
        LiveCodeMount = $false
        
        # Enable container debugging
        EnableDebugging = $false
        
        # Additional debug ports to expose
        DebugPorts = @()
    }
}

# Export configuration for use by other scripts
return $Config