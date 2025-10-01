#!/bin/bash

# Set up environment
export DISPLAY=:99
export QT_QPA_PLATFORM=offscreen

# Function to show usage
show_usage() {
    echo "Facial Pose Animator - Maya Container Test Runner"
    echo "Usage:"
    echo "  podman run facial-pose-tests                      # Run all tests"
    echo "  podman run facial-pose-tests TestClassName        # Run specific test"
    echo "  podman run facial-pose-tests --verify             # Verify Maya works"
    echo "  podman run facial-pose-tests --help               # Show this help"
    echo ""
    echo "Mount volumes:"
    echo "  -v \$(pwd)/results:/app/test_results              # Get test results"
    echo ""
    echo "Examples:"
    echo "  podman run --rm facial-pose-tests"
    echo "  podman run --rm facial-pose-tests TestFacialPoseData"
    echo "  podman run --rm -v \$(pwd)/results:/app/test_results facial-pose-tests"
}

# Handle special arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
elif [ "$1" = "--verify" ]; then
    echo "Verifying Maya environment..."
    mayapy /app/tests/verify_maya.py
    exit $?
fi

# Default: run tests
echo "Starting Maya test environment..."
echo "Arguments: $@"

# Set working directory to tests and run the container test runner with mayapy
cd /app/tests
exec mayapy /app/tests/run_container_tests.py "$@"