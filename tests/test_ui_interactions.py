#!/usr/bin/env python
"""
Unit tests for facial_pose_creator.py UI interactions.

This module provides comprehensive unit tests for the FacialPoseCreatorUI class,
focusing on user interactions, validation, and error handling.

Tests are designed to run in standalone mode with mocked Maya dependencies.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import test fixtures
from conftest import qapp, mock_maya, mock_animator, ui_fixture, sample_pose_data, sample_control_selection
from facialposecreator import facial_pose_creator

# QMessageBox constants for testing
QMessageBox_Yes = 1
QMessageBox_No = 0


class TestRegisterButtonValidation:
    """Test cases for register button validation logic."""

    def test_register_button_no_selection(self, ui_fixture, mock_maya):
        """Test register button with no Maya selection."""
        # Setup
        ui = ui_fixture

        # Mock QMessageBox.warning to capture calls
        with patch('facialposecreator.facial_pose_creator.QMessageBox.warning') as mock_warning, \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True):
            # Execute
            ui.register_selected_control_btn.click()

            # Verify
            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args
            assert "No Selection" in args[1]  # title
            assert "select at least one facial control" in args[2]  # message

            # Verify UI state unchanged
            assert ui.state.current_driver is None

    def test_register_button_valid_controls(self, ui_fixture, mock_maya, mock_animator):
        """Test register button with valid control selection."""
        # Setup
        mock_control = MagicMock()
        mock_control.nodeType.return_value = 'transform'
        mock_control.nodeName.return_value = 'L_Eyebrow_CTRL'
        
        with patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True), \
             patch.object(ui_fixture, '_get_selected_controls', return_value=[mock_control]):            # Mock successful registration
            mock_driver = MagicMock()
            mock_driver.nodeName.return_value = 'FacialPoseValue'
            
            # Patch the safe_create_driver function
            with patch('facialposecreator.facial_pose_creator.safe_create_driver', return_value=mock_driver) as mock_safe_create:
                with patch.object(ui_fixture, 'refresh_pose_list') as mock_refresh:
                    with patch('facialposecreator.facial_pose_creator.QMessageBox.information') as mock_info:
                        ui = ui_fixture

                        # Execute
                        ui.register_selected_control_btn.click()

                        # Verify
                        mock_refresh.assert_called_once()
                        mock_info.assert_called_once()

                        # Verify success message
                        args, kwargs = mock_info.call_args
                        assert "Success" in args[1]  # title
                        assert "Registered" in args[2]  # message

                        # Verify UI state updated
                        assert ui.state.current_driver == mock_driver

    def test_register_button_duplicate_control(self, ui_fixture, mock_maya):
        """Test register button with already registered control."""
        # Setup
        mock_control = MagicMock()
        mock_control.nodeType.return_value = 'transform'
        mock_control.nodeName.return_value = 'L_Eyebrow_CTRL'
        
    def test_register_button_duplicate_control(self, ui_fixture, mock_maya):
        """Test register button with already registered control."""
        # Setup
        mock_control = MagicMock()
        mock_control.nodeType.return_value = 'transform'
        mock_control.nodeName.return_value = 'L_Eyebrow_CTRL'
        
        with patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True), \
             patch.object(ui_fixture, '_get_selected_controls', return_value=[mock_control]):

            # Mock driver creation failure (duplicate)
            with patch('facialposecreator.facial_pose_creator.safe_create_driver', return_value=None) as mock_safe_create:
                with patch('facialposecreator.facial_pose_creator.QMessageBox.critical') as mock_critical:
                    ui = ui_fixture

                    # Execute
                    ui.register_selected_control_btn.click()

                    # Verify
                    mock_safe_create.assert_called_once()
                    mock_critical.assert_called_once()

                    # Verify error message
                    args, kwargs = mock_critical.call_args
                    assert "Registration Failed" in args[1]  # title
                    assert "Failed to create driver node" in args[2]  # message

    def test_register_button_non_transform_filtering(self, ui_fixture, mock_maya):
        """Test register button filters out non-transform nodes."""
        # Setup: Mix of transform and non-transform nodes
        mock_transform = MagicMock()
        mock_transform.nodeType.return_value = 'transform'
        mock_transform.nodeName.return_value = 'L_Eyebrow_CTRL'

        mock_camera = MagicMock()
        mock_camera.nodeType.return_value = 'camera'
        mock_camera.name.return_value = 'persp'
        
        with patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True), \
             patch.object(ui_fixture, '_get_selected_controls', return_value=[mock_transform, mock_camera]):

            with patch('facialposecreator.facial_pose_creator.safe_create_driver', return_value=MagicMock()) as mock_safe_create:
                with patch.object(ui_fixture, 'refresh_pose_list'):
                    with patch('facialposecreator.facial_pose_creator.QMessageBox.warning') as mock_warning:
                        ui = ui_fixture

                        # Execute
                        ui.register_selected_control_btn.click()

                        # Verify warning dialog shown for invalid nodes
                        mock_warning.assert_called_once()
                        args, kwargs = mock_warning.call_args
                        assert "Invalid Selection" in args[1]  # title
                        assert "transform nodes" in args[2]  # message
                        assert "persp" in args[2]  # invalid node name

                        # Verify safe_create_driver was not called due to validation failure
                        mock_safe_create.assert_not_called()
                        # The call should only include valid controls


class TestPoseListDisplay:
    """Test cases for pose list display functionality."""

    def test_pose_list_display_all_poses(self, ui_fixture, mock_animator):
        """Test pose list displays all registered poses."""
        # Setup
        poses = [
            "L_Eyebrow_CTRL_ty_10",
            "L_Eyebrow_CTRL_ty_minus_10",
            "R_Eyebrow_CTRL_ty_10",
            "R_Eyebrow_CTRL_ty_minus_10"
        ]
        mock_animator.get_all_poses.return_value = poses
        ui = ui_fixture

        # Execute
        ui.refresh_pose_list()

        # Verify
        assert ui.pose_list.count() == 4
        for i, pose_name in enumerate(sorted(poses)):
            assert ui.pose_list.item(i).text() == pose_name

    def test_pose_list_sorting_alphabetical(self, ui_fixture, mock_animator):
        """Test pose list sorts poses alphabetically."""
        # Setup: Unsorted poses
        unsorted_poses = [
            "R_Eyebrow_CTRL_ty_10",
            "L_Eyebrow_CTRL_ty_10",
            "L_Eyebrow_CTRL_ty_minus_10",
            "R_Eyebrow_CTRL_ty_minus_10"
        ]
        expected_sorted = sorted(unsorted_poses)

        mock_animator.get_all_poses.return_value = unsorted_poses
        ui = ui_fixture

        # Execute
        ui.refresh_pose_list()

        # Verify alphabetical sorting
        for i, pose_name in enumerate(expected_sorted):
            assert ui.pose_list.item(i).text() == pose_name

    def test_pose_list_empty_state(self, ui_fixture, mock_animator):
        """Test pose list shows message when no poses."""
        # Setup
        mock_animator.get_all_poses.return_value = []
        ui = ui_fixture

        # Execute
        ui.refresh_pose_list()

        # Verify
        assert ui.pose_list.count() == 1
        assert "No poses available" in ui.pose_list.item(0).text()


class TestPoseSelection:
    """Test cases for pose selection and animation."""

    def test_pose_selection_triggers_animation(self, ui_fixture, mock_animator):
        """Test clicking pose in list animates controls."""
        # Setup
        pose_name = "L_Eyebrow_CTRL_ty_10"
        mock_animator.get_all_poses.return_value = [pose_name]

        with patch('facialposecreator.facial_pose_creator.safe_animate_poses') as mock_safe_animate:
            ui = ui_fixture
            ui.refresh_pose_list()

            # Execute: Simulate clicking the pose
            item = ui.pose_list.item(0)
            ui.on_pose_selected(item)

            # Verify
            mock_safe_animate.assert_called_once()
            assert ui.state.selected_pose == pose_name

    def test_pose_selection_handles_animation_failure(self, ui_fixture, mock_animator):
        """Test pose selection handles animation failure gracefully."""
        # Setup
        pose_name = "L_Eyebrow_CTRL_ty_10"
        mock_animator.get_all_poses.return_value = [pose_name]

        with patch('facialposecreator.facial_pose_creator.safe_animate_poses', return_value=False) as mock_safe_animate:
            with patch('facialposecreator.facial_pose_creator.QMessageBox.critical') as mock_critical:
                ui = ui_fixture
                ui.refresh_pose_list()

                # Execute
                item = ui.pose_list.item(0)
                ui.on_pose_selected(item)

                # Verify
                mock_safe_animate.assert_called_once()
                mock_critical.assert_called_once()

                # Verify error message
                args, kwargs = mock_critical.call_args
                assert "Pose Application Failed" in args[1]
                assert pose_name in args[2]


class TestUIInitialization:
    """Test cases for UI initialization and state management."""

    def test_ui_initialization_no_driver(self, ui_fixture, mock_animator):
        """Test UI initializes correctly when no driver exists."""
        # Setup
        mock_animator.get_all_poses.return_value = []
        ui = ui_fixture

        # Execute: UI is already initialized in fixture
        # Verify initial state
        assert ui.state.current_driver is None
        assert ui.state.selected_pose is None
        assert len(ui.state.preview_cache) == 0

        # Verify pose list shows empty message
        assert ui.poses_list.count() == 1
        assert "No poses available" in ui.poses_list.item(0).text()

    def test_ui_initialization_with_driver(self, ui_fixture, mock_animator):
        """Test UI initializes correctly when driver exists."""
        # Setup
        poses = ["L_Eyebrow_CTRL_ty_10", "L_Eyebrow_CTRL_ty_minus_10"]
        mock_animator.get_all_poses.return_value = poses

        mock_driver = MagicMock()
        mock_driver.nodeName.return_value = 'FacialPoseValue'

        ui = ui_fixture
        ui.state.current_driver = mock_driver

        # Execute
        ui.refresh_pose_list()

        # Verify
        assert ui.pose_list.count() == 2
        assert ui.pose_list.item(0).text() == "L_Eyebrow_CTRL_ty_10"
        assert ui.pose_list.item(1).text() == "L_Eyebrow_CTRL_ty_minus_10"


class TestErrorHandling:
    """Test cases for comprehensive error handling."""

    def test_unexpected_error_in_registration(self, ui_fixture, mock_maya):
        """Test unexpected errors during registration are handled."""
        # Setup
        mock_control = MagicMock()
        mock_control.nodeType.return_value = 'transform'
        mock_maya['pymel'].selected.return_value = [mock_control]

        # Mock unexpected exception
        with patch.object(facial_pose_creator, 'safe_create_driver', side_effect=Exception("Unexpected error")) as mock_safe_create:
            with patch('facialposecreator.facial_pose_creator.QMessageBox.critical') as mock_critical:
                ui = ui_fixture

                # Execute
                ui.register_selected_control_btn.click()

                # Verify
                mock_safe_create.assert_called_once()
                mock_critical.assert_called_once()

                # Verify error message
                args, kwargs = mock_critical.call_args
                assert "Unexpected Error" in args[1]
                assert "Unexpected error occurred" in args[2]
                assert "Check script editor for details" in args[2]

    def test_unexpected_error_in_pose_selection(self, ui_fixture, mock_animator):
        """Test unexpected errors during pose selection are handled."""
        # Setup
        pose_name = "L_Eyebrow_CTRL_ty_10"
        mock_animator.get_all_poses.return_value = [pose_name]

        with patch('facialposecreator.facial_pose_creator.safe_animate_poses', side_effect=Exception("Network error")) as mock_safe_animate:
            with patch('facialposecreator.facial_pose_creator.QMessageBox.critical') as mock_critical:
                ui = ui_fixture
                ui.refresh_pose_list()

                # Execute
                item = ui.pose_list.item(0)
                ui.on_pose_selected(item)

                # Verify
                mock_safe_animate.assert_called_once()
                mock_critical.assert_called_once()

                # Verify error message
                args, kwargs = mock_critical.call_args
                assert "Unexpected Error" in args[1]
                assert "Network error" in args[2]


# Integration test markers for tests requiring Maya
pytestmark_maya = pytest.mark.maya

class TestMayaIntegration:
    """Integration tests requiring Maya environment."""

    @pytest.mark.maya
    def test_register_button_creates_real_driver(self, ui_fixture):
        """Integration test: Register button creates real Maya driver node."""
        # This test requires Maya to be running
        # Setup: Create test control in Maya scene
        # Execute: Click register button
        # Verify: Driver node exists in Maya scene with pose attributes
        pytest.skip("Maya integration test - requires Maya environment")

    @pytest.mark.maya
    def test_pose_selection_animates_real_controls(self, ui_fixture):
        """Integration test: Pose selection animates real Maya controls."""
        # This test requires Maya to be running
        # Setup: Register control, select pose
        # Execute: Click pose in list
        # Verify: Control transforms to pose values
        pytest.skip("Maya integration test - requires Maya environment")


class TestExportButtonValidation:
    """Test cases for export button validation logic."""

    def test_export_button_no_poses_registered(self, ui_fixture, mock_maya):
        """Test export button with no poses registered."""
        # Setup
        ui = ui_fixture

        # Mock QMessageBox.warning to capture calls
        with patch('facialposecreator.facial_pose_creator.QMessageBox.warning') as mock_warning, \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True):
            # Execute
            ui.export_poses_btn.click()

            # Verify
            mock_warning.assert_called_once()
            args, kwargs = mock_warning.call_args
            assert "No Poses" in args[1]  # title
            assert "no poses registered" in args[2]  # message

    def test_export_button_no_file_path_selected(self, ui_fixture, mock_maya, mock_animator):
        """Test export button with poses registered but no file path selected."""
        # Setup
        ui = ui_fixture
        ui.state.current_driver = MagicMock()
        
        # Mock poses available
        mock_animator.saved_poses = {'pose1': MagicMock(), 'pose2': MagicMock()}
        
        # Mock QFileDialog.getSaveFileName to return empty path
        with patch('facialposecreator.facial_pose_creator.QFileDialog.getSaveFileName', return_value=('', '')), \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True):
            # Execute
            ui.export_poses_btn.click()

            # Verify - should not proceed without file path
            # (The actual export logic would be tested separately)

    def test_export_button_invalid_file_path(self, ui_fixture, mock_maya, mock_animator):
        """Test export button with invalid file path."""
        # Setup
        ui = ui_fixture
        ui.state.current_driver = MagicMock()
        
        # Mock poses available
        mock_animator.saved_poses = {'pose1': MagicMock(), 'pose2': MagicMock()}
        
        # Mock QFileDialog.getSaveFileName to return invalid path
        invalid_path = 'Z:\\nonexistent\\drive\\file.fbx'
        with patch('facialposecreator.facial_pose_creator.QFileDialog.getSaveFileName', return_value=(invalid_path, 'FBX Files (*.fbx)')), \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True), \
             patch('facialposecreator.facial_pose_creator.QMessageBox.critical') as mock_critical:
            # Execute
            ui.export_poses_btn.click()

            # Verify error dialog shown
            mock_critical.assert_called_once()
            args, kwargs = mock_critical.call_args
            assert "Export Failed" in args[1]  # title
            assert "invalid" in args[2].lower() or "path" in args[2].lower()  # message

    def test_export_button_file_already_exists_no_overwrite(self, ui_fixture, mock_maya, mock_animator):
        """Test export button when file exists and user chooses not to overwrite."""
        # Setup
        ui = ui_fixture
        ui.state.current_driver = MagicMock()
        
        # Mock poses available
        mock_animator.saved_poses = {'pose1': MagicMock(), 'pose2': MagicMock()}
        
        # Mock file exists and user cancels overwrite
        existing_file = 'C:\\test\\export.fbx'
        with patch('facialposecreator.facial_pose_creator.QFileDialog.getSaveFileName', return_value=(existing_file, 'FBX Files (*.fbx)')), \
             patch('facialposecreator.facial_pose_creator.os.path.exists', return_value=True), \
             patch('facialposecreator.facial_pose_creator.QMessageBox.question', return_value=QMessageBox_No), \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True):
            # Execute
            ui.export_poses_btn.click()

            # Verify - should not proceed with export
            # (The export logic should be cancelled)

    def test_export_button_successful_validation(self, ui_fixture, mock_maya, mock_animator):
        """Test export button with valid setup proceeds to export."""
        # Setup
        ui = ui_fixture
        ui.state.current_driver = MagicMock()
        
        # Mock poses available
        mock_animator.saved_poses = {'pose1': MagicMock(), 'pose2': MagicMock()}
        
        # Mock successful file selection and export
        export_file = 'C:\\test\\export.fbx'
        with patch('facialposecreator.facial_pose_creator.QFileDialog.getSaveFileName', return_value=(export_file, 'FBX Files (*.fbx)')), \
             patch('facialposecreator.facial_pose_creator.os.path.exists', return_value=False), \
             patch('facialposecreator.facial_pose_creator.MAYA_AVAILABLE', True), \
             patch.object(ui, 'perform_fbx_export') as mock_export:
            # Execute
            ui.export_poses_btn.click()

            # Verify export method called
            mock_export.assert_called_once_with(export_file, ['pose1', 'pose2'])


class TestFBXExportIntegration:
    """Integration tests for FBX export workflow."""

    def test_fbx_export_method_exists(self, mock_animator):
        """Test that the FBX export method exists on the animator."""
        # Verify the method exists
        assert hasattr(mock_animator, 'export_poses_to_fbx')
        assert callable(getattr(mock_animator, 'export_poses_to_fbx'))

    def test_fbx_export_with_no_poses_raises_error(self, mock_animator):
        """Test FBX export with no poses raises appropriate error."""
        mock_animator.saved_poses = {}
        
        with pytest.raises(Exception) as exc_info:
            mock_animator.export_poses_to_fbx("test.fbx")
        
        assert "No poses found" in str(exc_info.value)

    def test_fbx_export_with_valid_poses_calls_methods(self, mock_animator, monkeypatch):
        """Test FBX export workflow calls expected methods."""
        # Setup mock poses
        mock_animator.saved_poses = {'pose1': MagicMock(), 'pose2': MagicMock()}
        
        # Mock the helper methods
        mock_get_bones = MagicMock(return_value=['bone1', 'bone2'])
        mock_clear_anim = MagicMock()
        mock_gen_mapping = MagicMock()
        mock_export_fbx = MagicMock()
        
        monkeypatch.setattr(mock_animator, '_get_facial_bones_for_export', mock_get_bones)
        monkeypatch.setattr(mock_animator, '_clear_animation_on_bones', mock_clear_anim)
        monkeypatch.setattr(mock_animator, '_generate_pose_mapping_file', mock_gen_mapping)
        monkeypatch.setattr(mock_animator, '_export_fbx_animation', mock_export_fbx)
        
        # Mock PyMEL functions
        mock_pm = MagicMock()
        monkeypatch.setattr('facialposecreator.facial_pose_animator.pm', mock_pm)
        
        # Execute
        mock_animator.export_poses_to_fbx("test.fbx", ['pose1', 'pose2'])
        
        # Verify calls
        mock_get_bones.assert_called_once()
        mock_clear_anim.assert_called_once_with(['bone1', 'bone2'])
        mock_gen_mapping.assert_called_once_with("test.fbx", ['pose1', 'pose2'])
        mock_export_fbx.assert_called_once()
        
        # Verify PyMEL timeline setup
        mock_pm.playbackOptions.assert_called_once_with(min=0, max=1)
        assert mock_pm.currentTime.call_count >= 2  # Called for each frame


if __name__ == '__main__':
    pytest.main([__file__])