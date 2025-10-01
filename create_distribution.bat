@echo off
REM Create Distribution Package for Facial Pose Tools
REM This batch file is a Windows alternative to the PowerShell script

setlocal enabledelayedexpansion

echo =====================================
echo Facial Pose Tools - Create Distribution
echo =====================================
echo.

set VERSION=1.0.0
set OUTPUT_DIR=.\dist
set DIST_NAME=FacialPoseTools_v%VERSION%
set OUTPUT_PATH=%OUTPUT_DIR%\%DIST_NAME%

REM Create output directory
echo [1/6] Creating output directory...
if exist "%OUTPUT_DIR%" (
    echo   Cleaning existing dist directory...
    rmdir /s /q "%OUTPUT_DIR%" 2>nul
)
mkdir "%OUTPUT_PATH%" 2>nul
echo   [OK] Created: %OUTPUT_PATH%

REM Copy installer
echo.
echo [2/6] Copying installer...
copy "install.py" "%OUTPUT_PATH%\" >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Failed to copy install.py
    goto :error
)
echo   [OK] Copied install.py

REM Copy uninstaller
copy "uninstall.py" "%OUTPUT_PATH%\" >nul 2>&1
if errorlevel 1 (
    echo   [WARNING] Failed to copy uninstall.py
) else (
    echo   [OK] Copied uninstall.py
)

REM Copy source files
echo.
echo [3/6] Copying source files...
if exist "src" (
    xcopy /E /I /Y /Q "src" "%OUTPUT_PATH%\src\" >nul 2>&1
    if errorlevel 1 (
        echo   [ERROR] Failed to copy src directory
        goto :error
    )
    echo   [OK] Copied src directory
    
    REM Remove __pycache__ directories
    for /d /r "%OUTPUT_PATH%" %%d in (__pycache__) do (
        if exist "%%d" rmdir /s /q "%%d" 2>nul
    )
    echo   [OK] Cleaned __pycache__ directories
    
    REM Remove .pyc files
    del /s /q "%OUTPUT_PATH%\*.pyc" >nul 2>&1
    echo   [OK] Removed .pyc files
) else (
    echo   [WARNING] src directory not found
)

REM Copy documentation
echo.
echo [4/6] Copying documentation...
set DOCS=INSTALL.md README.md MIGRATION_SUMMARY.md
for %%f in (%DOCS%) do (
    if exist "%%f" (
        copy "%%f" "%OUTPUT_PATH%\" >nul 2>&1
        echo   [OK] Copied %%f
    )
)

REM Create quick start guide
echo.
echo [5/6] Creating quick start guide...
(
echo FACIAL POSE TOOLS - QUICK START
echo ================================
echo.
echo Installation:
echo 1. Extract this zip file
echo 2. Open Autodesk Maya
echo 3. Drag and drop 'install.py' into Maya's viewport
echo 4. Follow the installation prompts
echo.
echo Usage:
echo 1. Click the 'Face' button on the Custom shelf
echo 2. Or run in Script Editor:
echo    import facialposecreator
echo    facialposecreator.show_ui^(^)
echo.
echo For detailed instructions, see INSTALL.md
echo.
echo Version: %VERSION%
echo Author: Nguyen Phi Hung
echo Date: %date%
) > "%OUTPUT_PATH%\QUICKSTART.txt"
echo   [OK] Created QUICKSTART.txt

REM Create zip file (requires PowerShell for compression)
echo.
echo [6/6] Creating zip archive...
set ZIP_PATH=%OUTPUT_DIR%\%DIST_NAME%.zip
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%" 2>nul

powershell -Command "Compress-Archive -Path '%OUTPUT_PATH%' -DestinationPath '%ZIP_PATH%' -CompressionLevel Optimal" >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Failed to create zip archive
    echo   Note: PowerShell is required for creating zip files
    goto :error
)
echo   [OK] Created: %ZIP_PATH%

REM Calculate file size
for %%A in ("%ZIP_PATH%") do set ZIP_SIZE=%%~zA
set /a ZIP_SIZE_MB=!ZIP_SIZE! / 1048576

REM Summary
echo.
echo =====================================
echo [SUCCESS] Distribution Package Created!
echo =====================================
echo.
echo Package Details:
echo   Name:     %DIST_NAME%.zip
echo   Location: %ZIP_PATH%
echo   Size:     !ZIP_SIZE_MB! MB
echo.
echo Package Contents:
dir /s /b "%OUTPUT_PATH%\*" | findstr /v "__pycache__"
echo.
echo Distribution Instructions:
echo   1. Share the zip file: %DIST_NAME%.zip
echo   2. Users should extract the zip
echo   3. Drag install.py into Maya viewport
echo   4. The tool will be installed automatically
echo.
echo [OK] Done!
echo.

REM Ask to open directory
set /p OPEN_DIR="Open output directory? (Y/N): "
if /i "%OPEN_DIR%"=="Y" start "" "%OUTPUT_DIR%"

goto :end

:error
echo.
echo [ERROR] Distribution creation failed!
echo.
pause
exit /b 1

:end
pause
exit /b 0
