# Dockerfile for running Facial Pose Animator tests in Maya environment
# Uses mottosso/docker-maya as base image to provide Maya environment
#
# Build with:
#   podman build -t facial-pose-tests .
#
# Run with:
#   podman run --rm facial-pose-tests
#   podman run --rm facial-pose-tests TestFacialPoseData  # Run specific test class
#   podman run --rm -v $(pwd)/test_results:/app/test_results facial-pose-tests --output-dir /app/test_results

FROM mottosso/maya:2024

# Set maintainer info
LABEL maintainer="Facial Pose Animator Test Suite"
LABEL description="Maya environment for testing facial_pose_animator.py"
LABEL version="1.0"

# Set environment variables
ENV MAYA_DISABLE_CIP=1
ENV MAYA_DISABLE_CER=1
ENV MAYA_DISABLE_CLIC_IPM=1
ENV PYTHONPATH=/app/src:/app/tests:$PYTHONPATH
ENV MAYA_SCRIPT_PATH=/app

# Create app directory
WORKDIR /app

# Copy requirements file first (for better Docker layer caching)
COPY tests/requirements.txt /app/

# Install Python dependencies using mayapy
# Upgrade pip first for better compatibility
RUN mayapy -m pip install --upgrade pip

# Install dependencies from requirements file
RUN mayapy -m pip install -r /app/requirements.txt

# Copy source code and tests
COPY src/ /app/src/
COPY tests/test_facial_pose_animator.py /app/tests/
COPY tests/run_tests_with_mayapy.py /app/tests/

# Create test results and tests directories
RUN mkdir -p /app/test_results /app/tests

# Copy container-specific scripts
COPY tests/run_container_tests.py /app/tests/
COPY tests/verify_maya.py /app/tests/
COPY tests/entrypoint.sh /app/

# Make scripts executable
RUN chmod +x /app/tests/run_container_tests.py /app/tests/verify_maya.py /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD []

# Health check to ensure Maya is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD mayapy /app/tests/verify_maya.py || exit 1