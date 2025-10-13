#!/usr/bin/env python
"""
Pytest configuration and shared fixtures for facial pose creator tests.

This module provides common test fixtures and configuration for both
unit tests and integration tests.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Try to import PySide6, fallback to PySide2
try:
    from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QListWidget, QLabel
    from PySide6.QtCore import Qt
    PYSIDE_VERSION = 6
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QListWidget, QLabel
        from PySide2.QtCore import Qt
        PYSIDE_VERSION = 2
    except ImportError:
        PYSIDE_VERSION = None

# Mock Maya modules for standalone testing
maya_mock = MagicMock()
maya_mock.selected.return_value = []
maya_mock.objExists.return_value = False
maya_mock.PyNode = MagicMock()

# Mock PyMEL
pymel_mock = MagicMock()
pymel_mock.selected.return_value = []
pymel_mock.objExists.return_value = False
pymel_mock.PyNode = MagicMock()

# Mock cmds
cmds_mock = MagicMock()
cmds_mock.selected.return_value = []

@pytest.fixture(scope="session")
def qapp():
    """Provide QApplication instance for Qt widget tests."""
    if PYSIDE_VERSION is None:
        pytest.skip("PySide2 or PySide6 not available")

    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield app

    # Clean up
    app.processEvents()

@pytest.fixture
def mock_maya():
    """Mock Maya environment for standalone testing."""
    with patch.dict('sys.modules', {
        'maya.cmds': maya_mock,
        'pymel.core': pymel_mock,
        'maya': maya_mock
    }):
        # Reset mocks
        maya_mock.reset_mock()
        pymel_mock.reset_mock()
        cmds_mock.reset_mock()

        # Configure common return values
        maya_mock.selected.return_value = []
        pymel_mock.selected.return_value = []
        maya_mock.objExists.return_value = False
        pymel_mock.objExists.return_value = False

        yield {
            'maya': maya_mock,
            'pymel': pymel_mock,
            'cmds': cmds_mock
        }

@pytest.fixture
def mock_animator():
    """Mock FacialPoseAnimator for UI testing."""
    animator = MagicMock()

    # Configure common return values
    animator.get_all_poses.return_value = []
    animator.create_pose_driver.return_value = MagicMock()
    animator.apply_pose.return_value = True

    return animator

@pytest.fixture
def ui_fixture(qapp, mock_maya, mock_animator):
    """Create FacialPoseCreatorUI instance with mocked dependencies."""
    if PYSIDE_VERSION is None:
        pytest.skip("PySide2 or PySide6 not available")

    # Import here to avoid import errors when PySide not available
    from facialposecreator.facial_pose_creator import FacialPoseCreatorUI

    # Mock the animator import
    with patch('facialposecreator.facial_pose_creator.facial_pose_animator') as mock_module:
        mock_module.FacialPoseAnimator = MagicMock(return_value=mock_animator)
        mock_module.safe_create_driver = MagicMock(return_value=MagicMock())
        mock_module.safe_register_selected_to_driver = MagicMock(return_value={
            'success': True,
            'total_items': 1,
            'total_controls': 1,
            'registered_controls': 1,
            'total_poses': 2,
            'controls_registered': ['test_ctrl'],
            'controls_skipped': [],
            'object_sets_processed': [],
            'errors': []
        })
        mock_module.safe_animate_poses = MagicMock(return_value=True)

        # Create UI instance
        ui = FacialPoseCreatorUI()

        yield ui

        # Clean up
        ui.close()

@pytest.fixture
def sample_pose_data():
    """Provide sample pose data for testing."""
    return {
        "name": "L_Eyebrow_CTRL_ty_10",
        "attribute_name": "L_Eyebrow_CTRL_ty_10",
        "description": "Left eyebrow raised",
        "timestamp": "2025-10-12T10:00:00",
        "maya_version": "2025",
        "controls": {
            "L_Eyebrow_CTRL": {
                "translateY": 10.0
            }
        }
    }

@pytest.fixture
def sample_control_selection(mock_maya):
    """Mock Maya selection with facial controls."""
    # Create mock control nodes
    mock_control = MagicMock()
    mock_control.nodeType.return_value = 'transform'
    mock_control.nodeName.return_value = 'L_Eyebrow_CTRL'

    # Configure selection
    mock_maya['pymel'].selected.return_value = [mock_control]

    return [mock_control]

@pytest.fixture
def temp_test_dir(tmp_path):
    """Provide temporary directory for test files."""
    test_dir = tmp_path / "facial_pose_tests"
    test_dir.mkdir()
    return test_dir