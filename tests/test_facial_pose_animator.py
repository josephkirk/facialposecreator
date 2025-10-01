#!/usr/bin/env python
"""
Unit tests for facial_pose_animator.py

This module provides comprehensive unit tests for the FacialPoseAnimator system,
including tests for all major classes, methods, and functionality.

Designed to run in a real Maya environment with PyMEL available.

Author: Test Suite
Date: Created for testing facial_pose_animator.py
"""

import unittest
import sys
import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the current directory to sys.path so we can import the module under test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Maya modules - these should be available in Maya environment
import maya.cmds as cmds
import pymel.core as pm

# Import the module under test
from facialposecreator.facial_pose_animator import (
    FacialPoseAnimator, FacialPoseData, ControlSelectionMode,
    FacialAnimatorError, ControlSelectionError, InvalidAttributeError,
    DriverNodeError, FileOperationError, ObjectSetError, PoseDataError,
    create_facial_animator, quick_reset_facial_controls,
    save_pose_from_selection, apply_saved_pose
)


def create_test_scene():
    """Create a test Maya scene with facial controls for testing."""
    # Clear scene
    cmds.file(new=True, force=True)
    
    # Create test facial controls
    test_controls = []
    
    # Create main facial controls with CTRL suffix to match pattern
    face_ctrl = cmds.circle(name="face_CTRL", radius=2)[0]
    mouth_ctrl = cmds.circle(name="mouth_CTRL", radius=1)[0]
    eye_l_ctrl = cmds.circle(name="eye_L_CTRL", radius=0.5)[0]
    eye_r_ctrl = cmds.circle(name="eye_R_CTRL", radius=0.5)[0]
    
    test_controls.extend([face_ctrl, mouth_ctrl, eye_l_ctrl, eye_r_ctrl])
    
    # Position controls
    cmds.move(0, 0, 0, face_ctrl)
    cmds.move(0, -1, 1, mouth_ctrl)
    cmds.move(-1, 1, 1, eye_l_ctrl)
    cmds.move(1, 1, 1, eye_r_ctrl)
    
    # Add some custom attributes for testing
    for ctrl in test_controls:
        cmds.addAttr(ctrl, ln="smile", at="double", min=-1, max=1, dv=0, k=True)
        cmds.addAttr(ctrl, ln="frown", at="double", min=-1, max=1, dv=0, k=True)
    
    return test_controls


def cleanup_test_scene():
    """Clean up test scene."""
    # Clear scene
    cmds.file(new=True, force=True)


class TestFacialPoseData(unittest.TestCase):
    """Test cases for FacialPoseData dataclass."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_controls = {
            "face_ctrl": {
                "translateX": 0.5,
                "rotateY": 1.2
            },
            "mouth_ctrl": {
                "translateZ": -0.3,
                "rotateX": 0.8
            }
        }
        
        self.pose_data = FacialPoseData(
            name="Test Pose",
            attribute_name="test_pose",
            controls=self.sample_controls,
            description="A test pose",
            timestamp="2024-01-01T12:00:00",
            maya_version="2024"
        )
    
    def test_initialization(self):
        """Test FacialPoseData initialization."""
        self.assertEqual(self.pose_data.name, "Test Pose")
        self.assertEqual(self.pose_data.attribute_name, "test_pose")
        self.assertEqual(self.pose_data.controls, self.sample_controls)
        self.assertEqual(self.pose_data.description, "A test pose")
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = self.pose_data.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], "Test Pose")
        self.assertEqual(result['controls'], self.sample_controls)
        
    def test_from_dict(self):
        """Test creation from dictionary."""
        data_dict = {
            'name': 'Dict Pose',
            'attribute_name': 'dict_pose',
            'controls': self.sample_controls,
            'description': 'Created from dict',
            'timestamp': '2024-01-01T12:00:00',
            'maya_version': '2024'
        }
        
        pose = FacialPoseData.from_dict(data_dict)
        
        self.assertEqual(pose.name, 'Dict Pose')
        self.assertEqual(pose.controls, self.sample_controls)
        
    def test_is_valid(self):
        """Test pose validation."""
        # Valid pose
        self.assertTrue(self.pose_data.is_valid())
        
        # Invalid poses
        invalid_pose1 = FacialPoseData("", "test", {})
        self.assertFalse(invalid_pose1.is_valid())
        
        invalid_pose2 = FacialPoseData("Test", "", {})
        self.assertFalse(invalid_pose2.is_valid())
        
        invalid_pose3 = FacialPoseData("Test", "test", {})
        self.assertFalse(invalid_pose3.is_valid())
        
    def test_get_control_count(self):
        """Test control count calculation."""
        self.assertEqual(self.pose_data.get_control_count(), 2)
        
    def test_get_attribute_count(self):
        """Test attribute count calculation."""
        self.assertEqual(self.pose_data.get_attribute_count(), 4)
        
    def test_has_control(self):
        """Test control existence check."""
        self.assertTrue(self.pose_data.has_control("face_ctrl"))
        self.assertTrue(self.pose_data.has_control("mouth_ctrl"))
        self.assertFalse(self.pose_data.has_control("nonexistent_ctrl"))
        
    def test_get_control_attributes(self):
        """Test getting control attributes."""
        face_attrs = self.pose_data.get_control_attributes("face_ctrl")
        expected = {"translateX": 0.5, "rotateY": 1.2}
        self.assertEqual(face_attrs, expected)
        
        empty_attrs = self.pose_data.get_control_attributes("nonexistent")
        self.assertEqual(empty_attrs, {})
        
    def test_sanitize_attribute_name(self):
        """Test attribute name sanitization."""
        # Test normal name
        normal_pose = FacialPoseData("Normal", "normal_name", {})
        self.assertEqual(normal_pose.sanitize_attribute_name(), "normal_name")
        
        # Test name with spaces and special characters
        special_pose = FacialPoseData("Special", "test name!@#", {})
        sanitized = special_pose.sanitize_attribute_name()
        self.assertTrue(sanitized.replace('_', '').isalnum())
        
        # Test name starting with number
        number_pose = FacialPoseData("Number", "123test", {})
        sanitized = number_pose.sanitize_attribute_name()
        self.assertTrue(sanitized.startswith('_') or sanitized[0].isalpha())


class TestControlSelectionMode(unittest.TestCase):
    """Test cases for ControlSelectionMode enum."""
    
    def test_enum_values(self):
        """Test enum value definitions."""
        self.assertEqual(ControlSelectionMode.PATTERN.value, "pattern")
        self.assertEqual(ControlSelectionMode.SELECTION.value, "selection")
        self.assertEqual(ControlSelectionMode.OBJECT_SET.value, "object_set")
        self.assertEqual(ControlSelectionMode.METADATA.value, "metadata")


class TestCustomExceptions(unittest.TestCase):
    """Test cases for custom exception classes."""
    
    def test_exception_inheritance(self):
        """Test exception class inheritance."""
        self.assertTrue(issubclass(FacialAnimatorError, Exception))
        self.assertTrue(issubclass(ControlSelectionError, FacialAnimatorError))
        self.assertTrue(issubclass(InvalidAttributeError, FacialAnimatorError))
        self.assertTrue(issubclass(DriverNodeError, FacialAnimatorError))
        self.assertTrue(issubclass(FileOperationError, FacialAnimatorError))
        self.assertTrue(issubclass(ObjectSetError, FacialAnimatorError))
        self.assertTrue(issubclass(PoseDataError, FacialAnimatorError))
        
    def test_exception_raising(self):
        """Test that exceptions can be raised properly."""
        with self.assertRaises(ControlSelectionError):
            raise ControlSelectionError("Test message")
            
        with self.assertRaises(FacialAnimatorError):
            raise InvalidAttributeError("Test message")


class TestFacialPoseAnimatorInitialization(unittest.TestCase):
    """Test cases for FacialPoseAnimator initialization and basic methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        cleanup_test_scene()
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_scene()
        
    def test_initialization(self):
        """Test proper initialization of FacialPoseAnimator."""
        self.assertEqual(self.animator.last_key_time, 0)
        self.assertEqual(self.animator.facial_driver_node, "FacialPoseValue")
        self.assertEqual(self.animator.control_pattern, "::*_CTRL")
        self.assertEqual(self.animator.excluded_nodes, ["GUI", "pup"])
        self.assertEqual(self.animator.excluded_attributes, ["scaleX", "scaleY", "scaleZ"])
        self.assertEqual(self.animator.tolerance, 0.01)
        self.assertEqual(self.animator.default_selection_mode, ControlSelectionMode.PATTERN)
        self.assertIsNone(self.animator.default_object_set)
        self.assertTrue(self.animator.enable_undo_tracking)
        self.assertEqual(len(self.animator.saved_poses), 0)
        
    def test_is_valid_control(self):
        """Test control validation using real Maya objects."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Get PyNode objects
        valid_ctrl = pm.PyNode(test_controls[0])  # face_CTRL
        self.assertTrue(self.animator._is_valid_control(valid_ctrl))
        
        # Create controls with excluded names
        gui_ctrl = cmds.circle(name="GUI_control")[0]
        pup_ctrl = cmds.circle(name="pup_control")[0]
        
        gui_pynode = pm.PyNode(gui_ctrl)
        pup_pynode = pm.PyNode(pup_ctrl)
        
        self.assertFalse(self.animator._is_valid_control(gui_pynode))
        self.assertFalse(self.animator._is_valid_control(pup_pynode))
        
    def test_is_valid_attribute(self):
        """Test attribute validation using real Maya attributes."""
        # Create test scene
        test_controls = create_test_scene()
        ctrl = pm.PyNode(test_controls[0])
        
        # Test valid attribute
        valid_attr = ctrl.attr("translateX")
        self.assertTrue(self.animator._is_valid_attribute(valid_attr))
        
        # Test locked attribute
        locked_attr = ctrl.attr("translateY")
        locked_attr.lock()
        self.assertFalse(self.animator._is_valid_attribute(locked_attr))
        locked_attr.unlock()  # Clean up
        
        # Test excluded attribute
        excluded_attr = ctrl.attr("scaleX")
        self.assertFalse(self.animator._is_valid_attribute(excluded_attr))
        
    def test_validate_scene_setup(self):
        """Test scene setup validation with real Maya scene."""
        # Test with empty scene
        result = self.animator.validate_scene_setup()
        
        self.assertTrue(result["maya_available"])
        self.assertFalse(result["controls_found"])  # No controls match pattern in empty scene
        self.assertFalse(result["driver_node_exists"])
        self.assertFalse(result["scene_saved"])  # New untitled scene
        
        # Test with controls that match pattern
        create_test_scene()
        
        result = self.animator.validate_scene_setup()
        
        self.assertTrue(result["maya_available"])
        self.assertTrue(result["controls_found"])  # Should find CTRL controls now
        self.assertFalse(result["driver_node_exists"])  # Still no driver node
            
    def test_set_default_selection_mode(self):
        """Test setting default selection mode."""
        self.animator.set_default_selection_mode(ControlSelectionMode.SELECTION)
        self.assertEqual(self.animator.default_selection_mode, ControlSelectionMode.SELECTION)
        
        self.animator.set_default_selection_mode(ControlSelectionMode.OBJECT_SET, "test_set")
        self.assertEqual(self.animator.default_selection_mode, ControlSelectionMode.OBJECT_SET)
        self.assertEqual(self.animator.default_object_set, "test_set")


class TestControlSelection(unittest.TestCase):
    """Test cases for control selection methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        cleanup_test_scene()
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_scene()
        
    def test_get_controls_from_selection(self):
        """Test getting controls from Maya selection."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Test with valid selection
        pm.select([test_controls[0], test_controls[1]])
        
        result = self.animator._get_controls_from_selection()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].nodeName(), "face_CTRL")
        
        # Test empty selection
        pm.select(clear=True)
        
        with self.assertRaises(ControlSelectionError):
            self.animator._get_controls_from_selection()
            
    def test_get_controls_from_pattern(self):
        """Test getting controls from pattern matching."""
        # Create test scene
        test_controls = create_test_scene()
        
        result = self.animator._get_controls_from_pattern()
        
        self.assertGreaterEqual(len(result), 2)  # Should find face_CTRL and mouth_CTRL
        
        # Verify control names contain "CTRL"
        for ctrl in result:
            self.assertIn("CTRL", ctrl.nodeName())
        
        # Test with modified pattern that matches nothing
        original_pattern = self.animator.control_pattern
        self.animator.control_pattern = "::*_NONEXISTENT"
        
        with self.assertRaises(ControlSelectionError):
            self.animator._get_controls_from_pattern()
            
        # Restore original pattern
        self.animator.control_pattern = original_pattern
            
    def test_get_controls_from_object_set(self):
        """Test getting controls from object set."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Create an object set
        object_set = cmds.sets(name="test_control_set", empty=True)
        cmds.sets([test_controls[0], test_controls[1]], add=object_set)
        
        result = self.animator._get_controls_from_object_set("test_control_set")
        
        self.assertEqual(len(result), 2)
        
        # Test non-existent set
        with self.assertRaises(ObjectSetError):
            self.animator._get_controls_from_object_set("nonexistent_set")
            
    def test_get_facial_controls_with_modes(self):
        """Test get_facial_controls with different modes."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Test PATTERN mode
        result = self.animator.get_facial_controls(mode=ControlSelectionMode.PATTERN)
        self.assertGreaterEqual(len(result), 2)
        
        # Test SELECTION mode
        pm.select([test_controls[0]])
        result = self.animator.get_facial_controls(mode=ControlSelectionMode.SELECTION)
        self.assertEqual(len(result), 1)
        
        # Test OBJECT_SET mode
        object_set = cmds.sets(name="facial_control_set", empty=True)
        cmds.sets([test_controls[0]], add=object_set)
        result = self.animator.get_facial_controls(mode=ControlSelectionMode.OBJECT_SET, object_set_name="facial_control_set")
        self.assertEqual(len(result), 1)


class TestPoseManagement(unittest.TestCase):
    """Test cases for pose management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        cleanup_test_scene()
        
        # Create sample pose data
        self.sample_pose = FacialPoseData(
            name="Test Pose",
            attribute_name="test_pose",
            controls={
                "face_ctrl": {"translateX": 0.5, "rotateY": 1.2}
            },
            description="Test pose for unit tests"
        )
        self.animator.saved_poses["Test Pose"] = self.sample_pose
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_scene()
        
    def test_save_pose_from_selection(self):
        """Test saving pose from selection."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Set some attribute values
        ctrl_node = pm.PyNode(test_controls[0])
        ctrl_node.translateX.set(0.5)
        ctrl_node.rotateY.set(1.2)
        
        # Select the control
        pm.select([test_controls[0]])
        
        result = self.animator.save_pose_from_selection(
            "New Pose", 
            "Test description",
            auto_save_to_file=False
        )
        
        self.assertIsInstance(result, FacialPoseData)
        self.assertEqual(result.name, "New Pose")
        self.assertIn("New Pose", self.animator.saved_poses)
        self.assertIn("face_CTRL", result.controls)
        
    def test_apply_saved_pose(self):
        """Test applying saved pose."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Create a pose with real control data
        pose = FacialPoseData(
            name="Apply Test Pose",
            attribute_name="apply_test_pose",
            controls={
                "face_CTRL": {"translateX": 1.5, "translateY": 0.8}
            }
        )
        self.animator.saved_poses["Apply Test Pose"] = pose
        
        # Apply the pose
        result = self.animator.apply_saved_pose("Apply Test Pose")
        self.assertTrue(result)
        
        # Verify the values were applied
        ctrl_node = pm.PyNode("face_CTRL")
        self.assertAlmostEqual(ctrl_node.translateX.get(), 1.5, places=2)
        self.assertAlmostEqual(ctrl_node.translateY.get(), 0.8, places=2)
                
        # Test non-existent pose
        with self.assertRaises(PoseDataError):
            self.animator.apply_saved_pose("Nonexistent Pose")
            
    def test_list_saved_poses(self):
        """Test listing saved poses."""
        pose_list = self.animator.list_saved_poses()
        
        self.assertEqual(len(pose_list), 1)
        self.assertEqual(pose_list[0]['name'], "Test Pose")
        self.assertIn('control_count', pose_list[0])
        self.assertIn('attribute_count', pose_list[0])
        
    def test_remove_saved_pose(self):
        """Test removing saved pose."""
        # Remove existing pose
        result = self.animator.remove_saved_pose("Test Pose")
        self.assertTrue(result)
        self.assertNotIn("Test Pose", self.animator.saved_poses)
        
        # Try to remove non-existent pose
        result = self.animator.remove_saved_pose("Nonexistent")
        self.assertFalse(result)
        
    def test_get_pose_comparison(self):
        """Test pose comparison."""
        # Add second pose for comparison
        pose2 = FacialPoseData(
            name="Test Pose 2",
            attribute_name="test_pose_2",
            controls={
                "face_ctrl": {"translateX": 1.0, "rotateY": 1.2},  # Different translateX
                "other_ctrl": {"translateZ": 0.3}  # Unique control
            }
        )
        self.animator.saved_poses["Test Pose 2"] = pose2
        
        comparison = self.animator.get_pose_comparison("Test Pose", "Test Pose 2")
        
        self.assertEqual(comparison['pose1_name'], "Test Pose")
        self.assertEqual(comparison['pose2_name'], "Test Pose 2")
        self.assertEqual(comparison['common_controls'], 1)
        self.assertEqual(comparison['unique_to_pose2'], 1)
        
        # Test comparison with non-existent pose
        with self.assertRaises(PoseDataError):
            self.animator.get_pose_comparison("Test Pose", "Nonexistent")


class TestFileOperations(unittest.TestCase):
    """Test cases for file I/O operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Add sample pose
        self.sample_pose = FacialPoseData(
            name="File Test Pose",
            attribute_name="file_test_pose",
            controls={"ctrl": {"translateX": 0.5}}
        )
        self.animator.saved_poses["File Test Pose"] = self.sample_pose
        
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_export_poses_to_file(self):
        """Test exporting poses to file."""
        test_file = os.path.join(self.temp_dir, "test_poses.json")
        
        # Test successful export
        self.animator.export_poses_to_file(test_file)
        
        self.assertTrue(os.path.exists(test_file))
        
        # Verify file content
        with open(test_file, 'r') as f:
            data = json.load(f)
            
        self.assertIn('poses', data)
        self.assertIn('File Test Pose', data['poses'])
        
    def test_import_poses_from_file(self):
        """Test importing poses from file."""
        test_file = os.path.join(self.temp_dir, "import_test.json")
        
        # Create test file
        test_data = {
            'poses': {
                'Imported Pose': {
                    'name': 'Imported Pose',
                    'attribute_name': 'imported_pose',
                    'controls': {'ctrl': {'rotateX': 1.0}},
                    'description': 'Imported test pose',
                    'timestamp': '',
                    'maya_version': ''
                }
            }
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
            
        # Clear existing poses and import
        self.animator.saved_poses.clear()
        imported_names = self.animator.import_poses_from_file(test_file)
        
        self.assertEqual(len(imported_names), 1)
        self.assertIn('Imported Pose', imported_names)
        self.assertIn('Imported Pose', self.animator.saved_poses)
        
    def test_load_single_pose_from_file(self):
        """Test loading single pose from file."""
        test_file = os.path.join(self.temp_dir, "single_pose.json")
        
        # Create single pose file
        test_data = {
            'export_type': 'single_pose',
            'pose': {
                'name': 'Single Pose',
                'attribute_name': 'single_pose',
                'controls': {'ctrl': {'translateY': 0.3}},
                'description': 'Single pose test',
                'timestamp': '',
                'maya_version': ''
            }
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
            
        # Load the pose
        self.animator.saved_poses.clear()
        loaded_name = self.animator.load_single_pose_from_file(test_file)
        
        self.assertEqual(loaded_name, 'Single Pose')
        self.assertIn('Single Pose', self.animator.saved_poses)
        
    def test_write_pose_names(self):
        """Test writing pose names to file."""
        test_file = os.path.join(self.temp_dir, "pose_names.txt")
        pose_names = ["Pose1", "Pose2", "Pose3"]
        
        self.animator._write_pose_names(pose_names, test_file)
        
        self.assertTrue(os.path.exists(test_file))
        
        with open(test_file, 'r') as f:
            content = f.read()
            
        for pose_name in pose_names:
            self.assertIn(pose_name, content)


class TestUndoTracking(unittest.TestCase):
    """Test cases for undo tracking system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        
    def test_track_created_node(self):
        """Test node tracking."""
        self.animator._track_created_node("test_node")
        
        self.assertIn("test_node", self.animator.created_nodes)
        
    def test_track_created_connection(self):
        """Test connection tracking."""
        self.animator._track_created_connection("source.attr", "dest.attr")
        
        self.assertIn(("source.attr", "dest.attr"), self.animator.created_connections)
        
    def test_track_created_attribute(self):
        """Test attribute tracking."""
        self.animator._track_created_attribute("node", "attr")
        
        self.assertIn(("node", "attr"), self.animator.created_attributes)
        
    def test_clear_undo_tracking(self):
        """Test clearing undo tracking."""
        # Add some tracked items
        self.animator._track_created_node("node")
        self.animator._track_created_connection("src", "dst")
        self.animator._track_created_attribute("node", "attr")
        
        self.animator.clear_undo_tracking()
        
        self.assertEqual(len(self.animator.created_nodes), 0)
        self.assertEqual(len(self.animator.created_connections), 0)
        self.assertEqual(len(self.animator.created_attributes), 0)
        
    def test_set_undo_tracking(self):
        """Test enabling/disabling undo tracking."""
        # Add some tracked items
        self.animator._track_created_node("node")
        
        # Disable tracking
        self.animator.set_undo_tracking(False)
        
        self.assertFalse(self.animator.enable_undo_tracking)
        self.assertEqual(len(self.animator.created_nodes), 0)  # Should be cleared
        
        # Re-enable tracking
        self.animator.set_undo_tracking(True)
        
        self.assertTrue(self.animator.enable_undo_tracking)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        cleanup_test_scene()
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_scene()
    
    def test_create_facial_animator(self):
        """Test creating facial animator instance."""
        animator = create_facial_animator()
        
        self.assertIsInstance(animator, FacialPoseAnimator)
        
    def test_quick_reset_facial_controls(self):
        """Test quick reset function."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Set some non-default values
        ctrl = pm.PyNode(test_controls[0])
        ctrl.translateX.set(1.5)
        ctrl.translateY.set(2.0)
        ctrl.rotateZ.set(45.0)
        
        # Reset controls
        result = quick_reset_facial_controls()
        
        self.assertTrue(result)
        
        # Verify values were reset (should be close to zero)
        self.assertAlmostEqual(ctrl.translateX.get(), 0.0, places=2)
        self.assertAlmostEqual(ctrl.translateY.get(), 0.0, places=2)
        self.assertAlmostEqual(ctrl.rotateZ.get(), 0.0, places=2)
        
    def test_save_pose_from_selection_convenience(self):
        """Test convenience function for saving pose from selection."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Set some attribute values
        ctrl = pm.PyNode(test_controls[0])
        ctrl.translateX.set(0.5)
        
        # Select the control
        pm.select([test_controls[0]])
        
        result = save_pose_from_selection("Test Pose")
        
        self.assertIsInstance(result, FacialPoseData)
        self.assertEqual(result.name, "Test Pose")


class TestMayaOperationsReal(unittest.TestCase):
    """Test cases for Maya operations with real Maya environment."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        cleanup_test_scene()
        
    def tearDown(self):
        """Clean up after tests."""
        cleanup_test_scene()
        
    def test_reset_all_attributes(self):
        """Test resetting all attributes with real Maya objects."""
        # Create test scene
        test_controls = create_test_scene()
        
        # Set some non-default values
        for ctrl_name in test_controls:
            ctrl = pm.PyNode(ctrl_name)
            ctrl.translateX.set(1.0)
            ctrl.translateY.set(0.5)
            ctrl.rotateZ.set(30.0)
        
        # Reset all attributes
        self.animator.reset_all_attributes()
        
        # Verify all values are back to defaults (close to zero)
        for ctrl_name in test_controls:
            ctrl = pm.PyNode(ctrl_name)
            self.assertAlmostEqual(ctrl.translateX.get(), 0.0, places=2)
            self.assertAlmostEqual(ctrl.translateY.get(), 0.0, places=2)
            self.assertAlmostEqual(ctrl.rotateZ.get(), 0.0, places=2)


# Integration test suite runner
class FacialPoseAnimatorTestSuite:
    """Test suite runner for the facial pose animator tests."""
    
    @staticmethod
    def run_all_tests():
        """Run all test cases and return results."""
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestFacialPoseData,
            TestControlSelectionMode,
            TestCustomExceptions,
            TestFacialPoseAnimatorInitialization,
            TestControlSelection,
            TestPoseManagement,
            TestFileOperations,
            TestUndoTracking,
            TestConvenienceFunctions,
            TestMayaOperationsReal
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    @staticmethod
    def run_specific_test(test_class_name: str):
        """Run a specific test class."""
        import sys
        loader = unittest.TestLoader()
        
        # Try to get the test class from the current module
        current_module = sys.modules[__name__]
        if hasattr(current_module, test_class_name):
            test_class = getattr(current_module, test_class_name)
            suite = loader.loadTestsFromTestCase(test_class)
        else:
            # Fallback to name-based loading for __main__ context
            suite = loader.loadTestsFromName(f'__main__.{test_class_name}')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result


if __name__ == '__main__':
    # Run all tests when script is executed directly
    print("Running Facial Pose Animator Unit Tests")
    print("=" * 50)
    
    test_suite = FacialPoseAnimatorTestSuite()
    result = test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)