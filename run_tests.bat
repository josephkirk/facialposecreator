@echo off
REM Batch script to run facial_pose_animator unit tests with mayapy
REM
REM Usage:
REM   run_tests.bat                    - Run all tests
REM   run_tests.bat TestClassName      - Run specific test class
REM   run_tests.bat --integration      - Run integration tests
REM   run_tests.bat --no-maya          - Run mock tests only

echo Facial Pose Animator - Test Runner
echo ^=====================================

REM Try to find Maya installation automatically
set MAYAPY_FOUND=0

for %%L in ("C:\Program Files\Autodesk\Maya2024\bin" "C:\Program Files\Autodesk\Maya2023\bin" "C:\Program Files\Autodesk\Maya2022\bin" "C:\Program Files\Autodesk\Maya2025\bin" "C:\Program Files\Autodesk\Maya2026\bin") do (
    if exist "%%~L\mayapy.exe" (
        set "MAYAPY_PATH=%%~L\mayapy.exe"
        set MAYAPY_FOUND=1
        goto found_maya
    )
)

:found_maya
if %MAYAPY_FOUND%==1 (
    echo Found mayapy.exe at %MAYAPY_PATH%
    echo.
    
    REM Run the test script with mayapy
    "%MAYAPY_PATH%" "%~dp0run_tests_with_mayapy.py" %*
    
    echo.
    echo Test execution completed with exit code %ERRORLEVEL%
    
) else (
    echo ERROR: Could not find mayapy.exe in standard Maya installation locations.
    echo.
    echo Please ensure Maya is installed, or run manually with
    echo   "C:\Path\To\Maya\bin\mayapy.exe" "%~dp0run_tests_with_mayapy.py" %*
    echo.
    echo Alternatively, you can run the tests with regular Python (mock mode only)
    echo   python "%~dp0run_tests_with_mayapy.py" --no-maya %*
    
    REM Try to run with regular Python as fallback
    echo.
    echo Attempting to run with regular Python in mock mode...
    python "%~dp0run_tests_with_mayapy.py" --no-maya %*
)

pause