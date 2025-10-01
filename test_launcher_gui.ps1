# Facial Pose Animator - GUI Test Launcher
# Provides a simple Windows Forms interface for running container tests

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Import configuration
$ConfigPath = Join-Path $PSScriptRoot "container_config.ps1"
if (Test-Path $ConfigPath) {
    $Config = & $ConfigPath
} else {
    $Config = @{}
}

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Facial Pose Animator - Container Test Launcher"
$form.Size = New-Object System.Drawing.Size(600, 500)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.Icon = [System.Drawing.SystemIcons]::Application

# Main panel
$mainPanel = New-Object System.Windows.Forms.TableLayoutPanel
$mainPanel.Dock = "Fill"
$mainPanel.ColumnCount = 2
$mainPanel.RowCount = 12
$mainPanel.Padding = New-Object System.Windows.Forms.Padding(10)
$form.Controls.Add($mainPanel)

# Title label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "🚀 Container Test Configuration"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$titleLabel.AutoSize = $true
$titleLabel.Anchor = "Left"
$mainPanel.Controls.Add($titleLabel, 0, 0)
$mainPanel.SetColumnSpan($titleLabel, 2)

# Container Engine selection
$engineLabel = New-Object System.Windows.Forms.Label
$engineLabel.Text = "Container Engine:"
$engineLabel.AutoSize = $true
$engineLabel.Anchor = "Left"
$mainPanel.Controls.Add($engineLabel, 0, 1)

$engineCombo = New-Object System.Windows.Forms.ComboBox
$engineCombo.Items.AddRange(@("podman", "docker"))
$engineCombo.SelectedItem = if ($Config.ContainerEngine) { $Config.ContainerEngine } else { "podman" }
$engineCombo.DropDownStyle = "DropDownList"
$engineCombo.Anchor = "Left, Right"
$mainPanel.Controls.Add($engineCombo, 1, 1)

# Test Class selection
$testClassLabel = New-Object System.Windows.Forms.Label
$testClassLabel.Text = "Test Class (optional):"
$testClassLabel.AutoSize = $true
$testClassLabel.Anchor = "Left"
$mainPanel.Controls.Add($testClassLabel, 0, 2)

$testClassCombo = New-Object System.Windows.Forms.ComboBox
$testClasses = @(
    "",
    "TestFacialPoseData",
    "TestFacialPoseAnimatorInitialization", 
    "TestControlSelection",
    "TestPoseManagement",
    "TestFileOperations",
    "TestUndoTracking",
    "TestRealMayaOperations"
)
$testClassCombo.Items.AddRange($testClasses)
$testClassCombo.SelectedIndex = 0
$testClassCombo.Anchor = "Left, Right"
$mainPanel.Controls.Add($testClassCombo, 1, 2)

# Output Directory
$outputLabel = New-Object System.Windows.Forms.Label
$outputLabel.Text = "Output Directory:"
$outputLabel.AutoSize = $true
$outputLabel.Anchor = "Left"
$mainPanel.Controls.Add($outputLabel, 0, 3)

$outputTextBox = New-Object System.Windows.Forms.TextBox
$outputTextBox.Text = if ($Config.OutputDir) { $Config.OutputDir } else { "test_results" }
$outputTextBox.Anchor = "Left, Right"
$mainPanel.Controls.Add($outputTextBox, 1, 3)

# Checkboxes
$rebuildCheckBox = New-Object System.Windows.Forms.CheckBox
$rebuildCheckBox.Text = "Force Rebuild Container"
$rebuildCheckBox.AutoSize = $true
$rebuildCheckBox.Anchor = "Left"
$mainPanel.Controls.Add($rebuildCheckBox, 0, 4)
$mainPanel.SetColumnSpan($rebuildCheckBox, 2)

$verboseCheckBox = New-Object System.Windows.Forms.CheckBox
$verboseCheckBox.Text = "Verbose Output"
$verboseCheckBox.AutoSize = $true
$verboseCheckBox.Anchor = "Left"
$verboseCheckBox.Checked = if ($Config.DefaultVerbose) { $Config.DefaultVerbose } else { $false }
$mainPanel.Controls.Add($verboseCheckBox, 0, 5)
$mainPanel.SetColumnSpan($verboseCheckBox, 2)

$verifyCheckBox = New-Object System.Windows.Forms.CheckBox
$verifyCheckBox.Text = "Verify Maya Environment Only"
$verifyCheckBox.AutoSize = $true
$verifyCheckBox.Anchor = "Left"
$mainPanel.Controls.Add($verifyCheckBox, 0, 6)
$mainPanel.SetColumnSpan($verifyCheckBox, 2)

$cleanupCheckBox = New-Object System.Windows.Forms.CheckBox
$cleanupCheckBox.Text = "Clean Up After Testing"
$cleanupCheckBox.AutoSize = $true
$cleanupCheckBox.Anchor = "Left"
$mainPanel.Controls.Add($cleanupCheckBox, 0, 7)
$mainPanel.SetColumnSpan($cleanupCheckBox, 2)

$forceCheckBox = New-Object System.Windows.Forms.CheckBox
$forceCheckBox.Text = "Force Operations (Skip Confirmations)"
$forceCheckBox.AutoSize = $true
$forceCheckBox.Anchor = "Left"
$mainPanel.Controls.Add($forceCheckBox, 0, 8)
$mainPanel.SetColumnSpan($forceCheckBox, 2)

# Progress bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Style = "Marquee"
$progressBar.MarqueeAnimationSpeed = 0
$progressBar.Anchor = "Left, Right"
$progressBar.Visible = $false
$mainPanel.Controls.Add($progressBar, 0, 9)
$mainPanel.SetColumnSpan($progressBar, 2)

# Status label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Ready to run tests"
$statusLabel.AutoSize = $true
$statusLabel.Anchor = "Left"
$statusLabel.ForeColor = [System.Drawing.Color]::DarkBlue
$mainPanel.Controls.Add($statusLabel, 0, 10)
$mainPanel.SetColumnSpan($statusLabel, 2)

# Button panel
$buttonPanel = New-Object System.Windows.Forms.FlowLayoutPanel
$buttonPanel.FlowDirection = "LeftToRight"
$buttonPanel.Dock = "Fill"
$buttonPanel.WrapContents = $false
$mainPanel.Controls.Add($buttonPanel, 0, 11)
$mainPanel.SetColumnSpan($buttonPanel, 2)

# Run Tests button
$runButton = New-Object System.Windows.Forms.Button
$runButton.Text = "🚀 Run Tests"
$runButton.Size = New-Object System.Drawing.Size(120, 35)
$runButton.BackColor = [System.Drawing.Color]::LightGreen
$runButton.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$buttonPanel.Controls.Add($runButton)

# Open Results button
$openResultsButton = New-Object System.Windows.Forms.Button
$openResultsButton.Text = "📁 Open Results"
$openResultsButton.Size = New-Object System.Drawing.Size(120, 35)
$openResultsButton.BackColor = [System.Drawing.Color]::LightBlue
$buttonPanel.Controls.Add($openResultsButton)

# Help button
$helpButton = New-Object System.Windows.Forms.Button
$helpButton.Text = "❓ Help"
$helpButton.Size = New-Object System.Drawing.Size(80, 35)
$helpButton.BackColor = [System.Drawing.Color]::LightYellow
$buttonPanel.Controls.Add($helpButton)

# Exit button
$exitButton = New-Object System.Windows.Forms.Button
$exitButton.Text = "❌ Exit"
$exitButton.Size = New-Object System.Drawing.Size(80, 35)
$exitButton.BackColor = [System.Drawing.Color]::LightCoral
$buttonPanel.Controls.Add($exitButton)

# Event handlers
$runButton.Add_Click({
    # Disable controls during execution
    $runButton.Enabled = $false
    $progressBar.Visible = $true
    $progressBar.MarqueeAnimationSpeed = 30
    $statusLabel.Text = "Running tests..."
    $statusLabel.ForeColor = [System.Drawing.Color]::Orange
    
    # Build command arguments
    $scriptPath = Join-Path $PSScriptRoot "run_container_tests.ps1"
    $arguments = @()
    
    if ($testClassCombo.SelectedItem -and $testClassCombo.SelectedItem -ne "") {
        $arguments += "-TestClass", "'$($testClassCombo.SelectedItem)'"
    }
    
    $arguments += "-OutputDir", "'$($outputTextBox.Text)'"
    $arguments += "-ContainerEngine", $engineCombo.SelectedItem
    
    if ($rebuildCheckBox.Checked) { $arguments += "-Rebuild" }
    if ($verboseCheckBox.Checked) { $arguments += "-Verbose" }
    if ($verifyCheckBox.Checked) { $arguments += "-Verify" }
    if ($cleanupCheckBox.Checked) { $arguments += "-CleanUp" }
    if ($forceCheckBox.Checked) { $arguments += "-Force" }
    
    # Run in background
    $runspace = [powershell]::Create()
    $runspace.AddScript({
        param($ScriptPath, $Arguments)
        & powershell.exe -ExecutionPolicy Bypass -File $ScriptPath @Arguments
    }).AddArgument($scriptPath).AddArgument($arguments)
    
    $handle = $runspace.BeginInvoke()
    
    # Create timer to check completion
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 1000
    $timer.Add_Tick({
        if ($handle.IsCompleted) {
            try {
                $runspace.EndInvoke($handle) | Out-Null
                $runspace.Dispose()
                
                # Update UI
                $progressBar.MarqueeAnimationSpeed = 0
                $progressBar.Visible = $false
                $runButton.Enabled = $true
                
                if ($runspace.HadErrors) {
                    $statusLabel.Text = "Tests completed with errors"
                    $statusLabel.ForeColor = [System.Drawing.Color]::Red
                } else {
                    $statusLabel.Text = "Tests completed successfully!"
                    $statusLabel.ForeColor = [System.Drawing.Color]::Green
                }
                
                $timer.Stop()
                $timer.Dispose()
            }
            catch {
                $progressBar.MarqueeAnimationSpeed = 0
                $progressBar.Visible = $false
                $runButton.Enabled = $true
                $statusLabel.Text = "Test execution failed"
                $statusLabel.ForeColor = [System.Drawing.Color]::Red
                $timer.Stop()
                $timer.Dispose()
            }
        }
    })
    
    $timer.Start()
})

$openResultsButton.Add_Click({
    $resultsPath = Join-Path $PSScriptRoot $outputTextBox.Text
    if (Test-Path $resultsPath) {
        Start-Process "explorer.exe" -ArgumentList $resultsPath
    } else {
        [System.Windows.Forms.MessageBox]::Show("Results directory not found: $resultsPath", "Error", "OK", "Warning")
    }
})

$helpButton.Add_Click({
    $helpText = @"
Facial Pose Animator - Container Test Launcher

This GUI provides an easy way to run containerized Maya tests.

Configuration:
• Container Engine: Choose between Podman (recommended) or Docker
• Test Class: Run all tests or select a specific test class
• Output Directory: Where to save test results
• Options: Configure rebuild, verbosity, verification, cleanup, and force modes

Usage:
1. Configure your test settings using the controls above
2. Click 'Run Tests' to start the containerized test execution
3. Monitor progress and check results when complete
4. Use 'Open Results' to view detailed test output

The tests run in an isolated Maya 2024 container environment,
ensuring consistent and reproducible results.
"@
    [System.Windows.Forms.MessageBox]::Show($helpText, "Help", "OK", "Information")
})

$exitButton.Add_Click({
    $form.Close()
})

# Show the form
$form.ShowDialog() | Out-Null