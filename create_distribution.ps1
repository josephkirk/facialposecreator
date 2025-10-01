# Create Distribution Package for Facial Pose Tools
# This script creates a distributable zip file for easy installation

param(
    [string]$OutputDir = ".\dist",
    [string]$Version = "1.0.0"
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Facial Pose Tools - Create Distribution" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Get the project root directory
$ProjectRoot = $PSScriptRoot
$DistName = "FacialPoseTools_v$Version"
$OutputPath = Join-Path $OutputDir $DistName

# Create output directory
Write-Host "[1/6] Creating output directory..." -ForegroundColor Yellow
if (Test-Path $OutputDir) {
    Write-Host "  Cleaning existing dist directory..." -ForegroundColor Gray
    Remove-Item -Path $OutputDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
Write-Host "  ✓ Created: $OutputPath" -ForegroundColor Green

# Copy installer and uninstaller
Write-Host "`n[2/6] Copying installer and uninstaller..." -ForegroundColor Yellow
Copy-Item -Path (Join-Path $ProjectRoot "install.py") -Destination $OutputPath
Write-Host "  ✓ Copied install.py" -ForegroundColor Green

$UninstallPath = Join-Path $ProjectRoot "uninstall.py"
if (Test-Path $UninstallPath) {
    Copy-Item -Path $UninstallPath -Destination $OutputPath
    Write-Host "  ✓ Copied uninstall.py" -ForegroundColor Green
}

# Copy source files
Write-Host "`n[3/6] Copying source files..." -ForegroundColor Yellow
$SrcPath = Join-Path $ProjectRoot "src"
if (Test-Path $SrcPath) {
    Copy-Item -Path $SrcPath -Destination $OutputPath -Recurse
    Write-Host "  ✓ Copied src directory" -ForegroundColor Green
    
    # Remove __pycache__ directories
    Get-ChildItem -Path $OutputPath -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Write-Host "  ✓ Cleaned __pycache__ directories" -ForegroundColor Green
    
    # Remove .pyc files
    Get-ChildItem -Path $OutputPath -Recurse -File -Filter "*.pyc" | Remove-Item -Force
    Write-Host "  ✓ Removed .pyc files" -ForegroundColor Green
} else {
    Write-Host "  ✗ Warning: src directory not found" -ForegroundColor Red
}

# Copy documentation
Write-Host "`n[4/6] Copying documentation..." -ForegroundColor Yellow
$DocsFiles = @("INSTALL.md", "README.md", "MIGRATION_SUMMARY.md")
foreach ($doc in $DocsFiles) {
    $docPath = Join-Path $ProjectRoot $doc
    if (Test-Path $docPath) {
        Copy-Item -Path $docPath -Destination $OutputPath
        Write-Host "  ✓ Copied $doc" -ForegroundColor Green
    }
}

# Create a quick start guide
Write-Host "`n[5/6] Creating quick start guide..." -ForegroundColor Yellow
$QuickStartContent = @"
FACIAL POSE TOOLS - QUICK START
================================

Installation:
1. Extract this zip file
2. Open Autodesk Maya
3. Drag and drop 'install.py' into Maya's viewport
4. Follow the installation prompts

Usage:
1. Click the 'Face' button on the Custom shelf
2. Or run in Script Editor:
   import facialposecreator
   facialposecreator.show_ui()

For detailed instructions, see INSTALL.md

Version: $Version
Author: Nguyen Phi Hung
Date: $(Get-Date -Format "MMMM dd, yyyy")
"@

$QuickStartPath = Join-Path $OutputPath "QUICKSTART.txt"
$QuickStartContent | Out-File -FilePath $QuickStartPath -Encoding UTF8
Write-Host "  ✓ Created QUICKSTART.txt" -ForegroundColor Green

# Create zip file
Write-Host "`n[6/6] Creating zip archive..." -ForegroundColor Yellow
$ZipPath = Join-Path $OutputDir "$DistName.zip"
if (Test-Path $ZipPath) {
    Remove-Item -Path $ZipPath -Force
}

try {
    Compress-Archive -Path $OutputPath -DestinationPath $ZipPath -CompressionLevel Optimal
    Write-Host "  ✓ Created: $ZipPath" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Error creating zip: $_" -ForegroundColor Red
    exit 1
}

# Calculate file size
$ZipSize = (Get-Item $ZipPath).Length
$ZipSizeMB = [math]::Round($ZipSize / 1MB, 2)

# Summary
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "✓ Distribution Package Created!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package Details:" -ForegroundColor White
Write-Host "  Name:     $DistName.zip" -ForegroundColor Gray
Write-Host "  Location: $ZipPath" -ForegroundColor Gray
Write-Host "  Size:     $ZipSizeMB MB" -ForegroundColor Gray
Write-Host ""
Write-Host "Package Contents:" -ForegroundColor White

# List contents
Get-ChildItem -Path $OutputPath -Recurse | ForEach-Object {
    $relativePath = $_.FullName.Replace($OutputPath, "").TrimStart("\")
    if ($_.PSIsContainer) {
        Write-Host "  📁 $relativePath" -ForegroundColor Cyan
    } else {
        $fileSize = [math]::Round($_.Length / 1KB, 1)
        Write-Host "  📄 $relativePath ($fileSize KB)" -ForegroundColor Gray
    }
}

Write-Host "`nDistribution Instructions:" -ForegroundColor White
Write-Host "  1. Share the zip file: $DistName.zip" -ForegroundColor Gray
Write-Host "  2. Users should extract the zip" -ForegroundColor Gray
Write-Host "  3. Drag install.py into Maya viewport" -ForegroundColor Gray
Write-Host "  4. The tool will be installed automatically" -ForegroundColor Gray
Write-Host ""

# Optional: Open the output directory
$OpenDir = Read-Host "Open output directory? (Y/N)"
if ($OpenDir -eq "Y" -or $OpenDir -eq "y") {
    Invoke-Item $OutputDir
}

Write-Host "`n✓ Done!" -ForegroundColor Green
