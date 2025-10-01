@echo off
REM Facial Pose Animator - Container Testing Batch Wrapper
REM This batch file calls the PowerShell automation script

setlocal enabledelayedexpansion

REM Default values
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%run_container_tests.ps1"

REM Check if PowerShell script exists
if not exist "%PS_SCRIPT%" (
    echo ERROR: PowerShell script not found: %PS_SCRIPT%
    exit /b 1
)

REM Build PowerShell command with all arguments
set "PS_ARGS="
:parse_args
if "%~1"=="" goto execute
if "%~1"=="-h" set "PS_ARGS=%PS_ARGS% -Help" & shift & goto parse_args
if "%~1"=="--help" set "PS_ARGS=%PS_ARGS% -Help" & shift & goto parse_args
if "%~1"=="-v" set "PS_ARGS=%PS_ARGS% -Verbose" & shift & goto parse_args
if "%~1"=="--verbose" set "PS_ARGS=%PS_ARGS% -Verbose" & shift & goto parse_args
if "%~1"=="-r" set "PS_ARGS=%PS_ARGS% -Rebuild" & shift & goto parse_args
if "%~1"=="--rebuild" set "PS_ARGS=%PS_ARGS% -Rebuild" & shift & goto parse_args
if "%~1"=="--verify" set "PS_ARGS=%PS_ARGS% -Verify" & shift & goto parse_args
if "%~1"=="--cleanup" set "PS_ARGS=%PS_ARGS% -CleanUp" & shift & goto parse_args
if "%~1"=="--force" set "PS_ARGS=%PS_ARGS% -Force" & shift & goto parse_args
if "%~1"=="--docker" set "PS_ARGS=%PS_ARGS% -ContainerEngine docker" & shift & goto parse_args

REM Handle parameters with values
if "%~1"=="-t" (
    set "PS_ARGS=%PS_ARGS% -TestClass '%~2'"
    shift & shift & goto parse_args
)
if "%~1"=="--test" (
    set "PS_ARGS=%PS_ARGS% -TestClass '%~2'"
    shift & shift & goto parse_args
)
if "%~1"=="-o" (
    set "PS_ARGS=%PS_ARGS% -OutputDir '%~2'"
    shift & shift & goto parse_args
)
if "%~1"=="--output" (
    set "PS_ARGS=%PS_ARGS% -OutputDir '%~2'"
    shift & shift & goto parse_args
)

REM If we get here, it's an unknown argument - pass it through
set "PS_ARGS=%PS_ARGS% '%~1'"
shift
goto parse_args

:execute
echo Facial Pose Animator - Container Testing
echo ========================================
echo Calling PowerShell automation script...
echo.

REM Execute PowerShell script with arguments
powershell.exe -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %PS_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ========================================
if %EXIT_CODE% equ 0 (
    echo Automation completed successfully!
) else (
    echo Automation failed with exit code: %EXIT_CODE%
)

exit /b %EXIT_CODE%