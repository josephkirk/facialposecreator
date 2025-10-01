# Facial Pose Animator - Docker Container Testing

This directory contains a Dockerfile and supporting scripts to run the facial pose animator tests in a containerized Maya environment using Podman (or Docker).

## Overview

The container setup provides:
- **Maya 2024** environment via `mottosso/docker-maya` base image
- **Headless operation** suitable for CI/CD pipelines
- **Test result export** to host filesystem
- **Flexible test execution** (all tests, specific classes, verification)

## Prerequisites

### Install Podman (Recommended)
```bash
# Windows (using winget)
winget install RedHat.Podman

# Or download from: https://podman.io/getting-started/installation
```

### Alternative: Docker
If you prefer Docker instead of Podman, replace `podman` with `docker` in all commands below.

## Quick Start

### 1. Build the Container
```bash
# Navigate to the project directory
cd "g:\Projects\Dev\FacialPoseTools"

# Build the container image
podman build -t facial-pose-tests .
```

### 2. Run All Tests
```bash
# Run all tests (results printed to console)
podman run --rm facial-pose-tests

# Run tests and save results to host directory
mkdir results
podman run --rm -v $(pwd)/results:/app/test_results facial-pose-tests
```

### 3. Run Specific Tests
```bash
# Run a specific test class
podman run --rm facial-pose-tests TestFacialPoseData

# Run specific test with verbose output and save results
podman run --rm -v $(pwd)/results:/app/test_results facial-pose-tests TestPoseManagement --verbose
```

## Container Commands

### Basic Usage
```bash
# Show help
podman run --rm facial-pose-tests --help

# Verify Maya environment
podman run --rm facial-pose-tests --verify

# Run all tests
podman run --rm facial-pose-tests

# Run specific test class
podman run --rm facial-pose-tests TestFacialPoseData
```

### Advanced Usage
```bash
# Run tests with results saved to host
podman run --rm -v $(pwd)/results:/app/test_results facial-pose-tests

# Run specific test with verbose output
podman run --rm facial-pose-tests TestControlSelection --verbose

# Run with custom output directory inside container
podman run --rm -v $(pwd)/custom_results:/app/custom_output facial-pose-tests --output-dir /app/custom_output
```

## Container Features

### Environment Variables
The container sets up the following environment for headless Maya operation:
- `MAYA_DISABLE_CIP=1` - Disable Customer Improvement Program
- `MAYA_DISABLE_CER=1` - Disable Crash Error Reporting
- `MAYA_DISABLE_CLIC_IPM=1` - Disable license checking
- `DISPLAY=:99` - Virtual display for headless operation
- `QT_QPA_PLATFORM=offscreen` - Qt platform for headless GUI

### File Structure Inside Container
```
/app/
├── facial_pose_animator.py      # Main module being tested
├── test_facial_pose_animator.py # Test suite
├── run_container_tests.py       # Container-optimized test runner
├── verify_maya.py              # Maya environment verification
├── entrypoint.sh               # Container entry point
└── test_results/               # Default output directory
    ├── test.log               # Test execution log
    └── test_results.txt       # Detailed test results
```

### Health Check
The container includes a health check that verifies Maya is working properly:
```bash
# Check container health
podman ps --format "table {{.Names}} {{.Status}}"
```

## Output and Results

### Console Output
When tests run, you'll see output like:
```
Facial Pose Animator - Maya Container Test Runner
============================================================
2024-10-01 12:00:00,123 - INFO - Maya standalone initialized successfully in container
2024-10-01 12:00:01,456 - INFO - Running tests in Maya container environment

test_initialization (test_facial_pose_animator.TestFacialPoseData) ... ok
test_to_dict (test_facial_pose_animator.TestFacialPoseData) ... ok
...

============================================================
MAYA CONTAINER TEST RESULTS
============================================================
Tests run: 25
Failures: 0
Errors: 0
Success: True
Results written to: /app/test_results/test_results.txt
```

### Exported Results
When using volume mounting, results are saved to the host:

**test_results.txt**:
```
Maya Container Test Results
==================================================
Tests run: 25
Failures: 0
Errors: 0
Success: True

[Detailed failure/error information if any]
```

**test.log**:
```
2024-10-01 12:00:00,123 - INFO - Maya standalone initialized successfully in container
2024-10-01 12:00:01,456 - INFO - Running tests in Maya container environment
2024-10-01 12:00:05,789 - INFO - Maya environment cleaned up
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Facial Pose Animator

on: [push, pull_request]

jobs:
  test-maya:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build test container
      run: podman build -t facial-pose-tests .
    
    - name: Run tests
      run: |
        mkdir -p test_results
        podman run --rm -v $(pwd)/test_results:/app/test_results facial-pose-tests
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: test_results/
```

### GitLab CI Example
```yaml
test-maya:
  image: quay.io/podman/stable
  stage: test
  script:
    - podman build -t facial-pose-tests .
    - mkdir -p test_results
    - podman run --rm -v $(pwd)/test_results:/app/test_results facial-pose-tests
  artifacts:
    when: always
    paths:
      - test_results/
    expire_in: 1 week
```

## Troubleshooting

### Common Issues

1. **Container fails to build**
   ```bash
   # Check if base image is accessible
   podman pull mottosso/maya:2024
   
   # Build with verbose output
   podman build -t facial-pose-tests . --log-level debug
   ```

2. **Maya initialization fails**
   ```bash
   # Test Maya verification
   podman run --rm facial-pose-tests --verify
   
   # Check container logs
   podman run --rm facial-pose-tests --verbose
   ```

3. **Permission issues with volume mounting**
   ```bash
   # On Linux/WSL, ensure directory permissions
   mkdir -p results
   chmod 755 results
   
   # Use absolute paths
   podman run --rm -v /absolute/path/to/results:/app/test_results facial-pose-tests
   ```

4. **Test failures**
   ```bash
   # Run specific failing test with verbose output
   podman run --rm facial-pose-tests TestFailingClass --verbose
   
   # Check detailed logs
   podman run --rm -v $(pwd)/debug:/app/test_results facial-pose-tests --verbose
   cat debug/test.log
   ```

### Debugging

1. **Interactive container access**
   ```bash
   # Run container with shell access
   podman run --rm -it --entrypoint /bin/bash facial-pose-tests
   
   # Inside container, run Maya manually
   mayapy /app/verify_maya.py
   ```

2. **Container resource usage**
   ```bash
   # Monitor container resources
   podman stats
   
   # Check container processes
   podman top CONTAINER_ID
   ```

## Customization

### Using Different Maya Versions
Modify the Dockerfile to use a different base image:
```dockerfile
# Use Maya 2023 instead
FROM mottosso/maya:2023

# Or Maya 2025 (when available)
FROM mottosso/maya:2025
```

### Adding Custom Dependencies
```dockerfile
# Add custom Python packages
RUN mayapy -m pip install numpy scipy

# Or copy requirements file
COPY requirements.txt /app/
RUN mayapy -m pip install -r /app/requirements.txt
```

### Custom Test Configuration
Modify `run_container_tests.py` to add:
- Different logging levels
- Custom test discovery
- Performance benchmarking
- Test parallelization

## Performance Considerations

- **Container startup**: ~10-15 seconds (Maya initialization)
- **Full test suite**: ~2-5 minutes (depending on test complexity)
- **Memory usage**: ~2-4 GB (Maya + tests)
- **Disk space**: ~8 GB (base Maya image + dependencies)

For faster iteration during development, consider:
1. Running specific test classes instead of full suite
2. Using volume mounting for live code updates
3. Keeping containers running between test executions

## Security Notes

The container runs Maya in a controlled environment with:
- No network access to Maya licensing servers (uses MAYA_DISABLE_* env vars)
- Minimal file system access outside `/app`
- No persistent storage of Maya preferences or cache files
- Isolated from host Maya installations