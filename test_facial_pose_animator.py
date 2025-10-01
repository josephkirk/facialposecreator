#!/usr/bin/env python
"""
Unit tests for facial_pose_animator.py

This module provides comprehensive unit tests for the FacialPoseAnimator system,
including tests for all major classes, methods, and functionality.

Author: Test Suite
Date: Created for testing facial_pose_animator.py
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open, call
import sys
import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the current directory to sys.path so we can import the module under test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock PyMEL before importing the module under test
sys.modules['pymel'] = MagicMock()
sys.modules['pymel.core'] = MagicMock()

# Import the module under test
from facial_pose_animator import (
    FacialPoseAnimator, FacialPoseData, ControlSelectionMode,
    FacialAnimatorError, ControlSelectionError, InvalidAttributeError,
    DriverNodeError, FileOperationError, ObjectSetError, PoseDataError,
    create_facial_animator, quick_reset_facial_controls,
    save_pose_from_selection, apply_saved_pose
)

# Import pymel.core for mocking
import pymel.core as pm


class MockPyNode:
    """Mock class to simulate PyMEL PyNode objects."""
    
    def __init__(self, name: str, node_type: str = "transform"):
        self._name = name
        self._node_type = node_type
        self._attributes = {}
        self._locked = False
        self._connected = False
        self._hidden = False
        
    def nodeName(self) -> str:
        return self._name
        
    def __str__(self) -> str:
        return self._name
        
    def listAttr(self, k=False, v=False):
        """Mock listAttr method."""
        mock_attrs = []
        if k and v:  # keyable and visible
            for attr_name in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
                attr_mock = MockAttribute(f"{self._name}.{attr_name}", attr_name)
                mock_attrs.append(attr_mock)
        return mock_attrs
        
    def attr(self, attr_name: str):
        """Mock attr method."""
        return MockAttribute(f"{self._name}.{attr_name}", attr_name)


class MockAttribute:
    """Mock class to simulate PyMEL Attribute objects."""
    
    def __init__(self, full_name: str, attr_name: str):
        self._full_name = full_name
        self._attr_name = attr_name
        self._value = 0.0
        self._locked = False
        self._connected = False
        self._hidden = False
        self._type = "double"
        self._range = [-1.0, 1.0]
        
    def longName(self) -> str:
        return self._attr_name
        
    def attrName(self) -> str:
        return self._attr_name
        
    def isLocked(self) -> bool:
        return self._locked
        
    def isConnected(self) -> bool:
        return self._connected
        
    def isHidden(self) -> bool:
        return self._hidden
        
    def get(self, type=False):
        if type:
            return self._type
        return self._value
        
    def set(self, value: float):
        if not self._locked:
            self._value = value
            
    def getRange(self) -> List[float]:
        return self._range
        
    def node(self):
        node_name = self._full_name.split('.')[0]
        return MockPyNode(node_name)
        
    def inputs(self):
        return []
        
    def __rshift__(self, other):
        """Mock >> operator for connections."""
        pass


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
        """Test control validation."""
        # Valid control
        valid_ctrl = MockPyNode("face_CTRL")
        self.assertTrue(self.animator._is_valid_control(valid_ctrl))
        
        # Invalid controls (containing excluded nodes)
        gui_ctrl = MockPyNode("GUI_control")
        pup_ctrl = MockPyNode("pup_control")
        
        self.assertFalse(self.animator._is_valid_control(gui_ctrl))
        self.assertFalse(self.animator._is_valid_control(pup_ctrl))
        
    def test_is_valid_attribute(self):
        """Test attribute validation."""
        # Valid attribute
        valid_attr = MockAttribute("test.translateX", "translateX")
        self.assertTrue(self.animator._is_valid_attribute(valid_attr))
        
        # Invalid attributes
        locked_attr = MockAttribute("test.translateY", "translateY")
        locked_attr._locked = True
        self.assertFalse(self.animator._is_valid_attribute(locked_attr))
        
        connected_attr = MockAttribute("test.translateZ", "translateZ")
        connected_attr._connected = True
        self.assertFalse(self.animator._is_valid_attribute(connected_attr))
        
        excluded_attr = MockAttribute("test.scaleX", "scaleX")
        self.assertFalse(self.animator._is_valid_attribute(excluded_attr))
        
    @patch('facial_pose_animator.pm')
    def test_validate_scene_setup(self, mock_pm):
        """Test scene setup validation."""
        # Mock successful validation
        mock_pm.ls.return_value = []
        mock_pm.sceneName.return_value = "test_scene.ma"
        
        # Mock get_facial_controls to return some controls
        with patch.object(self.animator, 'get_facial_controls') as mock_get_controls:
            mock_get_controls.return_value = [MockPyNode("test_ctrl")]
            
            result = self.animator.validate_scene_setup()
            
            self.assertTrue(result["maya_available"])
            self.assertTrue(result["controls_found"])
            self.assertFalse(result["driver_node_exists"])  # No driver node in mock
            self.assertTrue(result["scene_saved"])
            
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
        
    @patch('facial_pose_animator.pm')
    def test_get_controls_from_selection(self, mock_pm):
        """Test getting controls from Maya selection."""
        # Mock selected objects
        mock_controls = [MockPyNode("ctrl1"), MockPyNode("ctrl2")]
        mock_pm.selected.return_value = mock_controls
        
        result = self.animator._get_controls_from_selection()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].nodeName(), "ctrl1")
        
        # Test empty selection
        mock_pm.selected.return_value = []
        
        with self.assertRaises(ControlSelectionError):
            self.animator._get_controls_from_selection()
            
    @patch('facial_pose_animator.pm')
    def test_get_controls_from_pattern(self, mock_pm):
        """Test getting controls from pattern matching."""
        # Mock pattern matching
        mock_controls = [MockPyNode("face_CTRL"), MockPyNode("mouth_CTRL")]
        mock_pm.ls.return_value = mock_controls
        
        result = self.animator._get_controls_from_pattern()
        
        self.assertEqual(len(result), 2)
        mock_pm.ls.assert_called_with("::*_CTRL", type='transform')
        
        # Test no matches
        mock_pm.ls.return_value = []
        
        with self.assertRaises(ControlSelectionError):
            self.animator._get_controls_from_pattern()
            
    @patch('facial_pose_animator.pm')
    def test_get_controls_from_object_set(self, mock_pm):
        """Test getting controls from object set."""
        # Mock object set operations
        mock_controls = [MockPyNode("ctrl1"), MockPyNode("ctrl2")]
        mock_set = MockPyNode("test_set", "objectSet")
        
        mock_pm.objExists.return_value = True
        mock_pm.PyNode.return_value = mock_set
        mock_pm.sets.return_value = mock_controls
        
        result = self.animator._get_controls_from_object_set("test_set")
        
        self.assertEqual(len(result), 2)
        
        # Test non-existent set
        mock_pm.objExists.return_value = False
        
        with self.assertRaises(ObjectSetError):
            self.animator._get_controls_from_object_set("nonexistent_set")
            
    @patch('facial_pose_animator.pm')
    def test_get_facial_controls_with_modes(self, mock_pm):
        """Test get_facial_controls with different modes."""
        mock_controls = [MockPyNode("face_CTRL")]
        
        # Test PATTERN mode
        with patch.object(self.animator, '_get_controls_from_pattern') as mock_pattern:
            mock_pattern.return_value = mock_controls
            
            result = self.animator.get_facial_controls(mode=ControlSelectionMode.PATTERN)
            self.assertEqual(len(result), 1)
            mock_pattern.assert_called_once()
            
        # Test SELECTION mode
        with patch.object(self.animator, '_get_controls_from_selection') as mock_selection:
            mock_selection.return_value = mock_controls
            
            result = self.animator.get_facial_controls(mode=ControlSelectionMode.SELECTION)
            self.assertEqual(len(result), 1)
            mock_selection.assert_called_once()


class TestPoseManagement(unittest.TestCase):
    """Test cases for pose management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animator = FacialPoseAnimator()
        
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
        
    @patch('facial_pose_animator.pm')
    def test_save_pose_from_selection(self, mock_pm):
        """Test saving pose from selection."""
        # Mock control selection and attribute values
        mock_control = MockPyNode("test_ctrl")
        mock_attrs = [MockAttribute("test_ctrl.translateX", "translateX")]
        mock_attrs[0]._value = 0.5  # Set non-zero value
        
        mock_control.listAttr = Mock(return_value=mock_attrs)
        
        with patch.object(self.animator, '_get_controls_from_selection') as mock_get_controls:
            mock_get_controls.return_value = [mock_control]
            
            with patch.object(self.animator, '_save_single_pose_to_file') as mock_save_file:
                result = self.animator.save_pose_from_selection(
                    "New Pose", 
                    "Test description",
                    auto_save_to_file=False
                )
                
                self.assertIsInstance(result, FacialPoseData)
                self.assertEqual(result.name, "New Pose")
                self.assertIn("New Pose", self.animator.saved_poses)
                
    def test_apply_saved_pose(self):
        """Test applying saved pose."""
        with patch('facial_pose_animator.pm') as mock_pm:
            # Mock control and attribute
            mock_control = MockPyNode("face_ctrl")
            mock_attr = MockAttribute("face_ctrl.translateX", "translateX")
            
            mock_pm.objExists.return_value = True
            mock_pm.PyNode.return_value = mock_control
            mock_pm.attributeQuery.return_value = True
            mock_control.attr = Mock(return_value=mock_attr)
            
            with patch.object(self.animator, 'undo_chunk_context') as mock_context:
                mock_context.__enter__ = Mock(return_value=self.animator)
                mock_context.__exit__ = Mock(return_value=None)
                
                result = self.animator.apply_saved_pose("Test Pose")
                
                self.assertTrue(result)
                
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
    
    def test_create_facial_animator(self):
        """Test creating facial animator instance."""
        animator = create_facial_animator()
        
        self.assertIsInstance(animator, FacialPoseAnimator)
        
    @patch('facial_pose_animator.FacialPoseAnimator')
    def test_quick_reset_facial_controls(self, mock_animator_class):
        """Test quick reset function."""
        mock_animator = Mock()
        mock_animator_class.return_value = mock_animator
        
        quick_reset_facial_controls()
        
        mock_animator_class.assert_called_once()
        mock_animator.reset_all_attributes.assert_called_once()
        
    @patch('facial_pose_animator.FacialPoseAnimator')
    def test_save_pose_from_selection_convenience(self, mock_animator_class):
        """Test convenience function for saving pose from selection."""
        mock_animator = Mock()
        mock_pose_data = Mock(spec=FacialPoseData)
        mock_animator.save_pose_from_selection.return_value = mock_pose_data
        mock_animator_class.return_value = mock_animator
        
        result = save_pose_from_selection("Test Pose")
        
        self.assertEqual(result, mock_pose_data)
        mock_animator.save_pose_from_selection.assert_called_once_with(
            "Test Pose", "", use_current_selection=True, 
            auto_save_to_file=True, output_directory=None
        )


class TestMayaOperationsMocked(unittest.TestCase):
    """Test cases for Maya operations with comprehensive mocking."""
    
    def setUp(self):
        """Set up test fixtures with Maya mocking."""
        self.animator = FacialPoseAnimator()
        
    @patch('facial_pose_animator.pm')
    def test_reset_all_attributes(self, mock_pm):
        """Test resetting all attributes with mocking."""
        # Mock controls and attributes
        mock_control = MockPyNode("test_ctrl")
        mock_attr = MockAttribute("test_ctrl.translateX", "translateX")
        mock_control.listAttr = Mock(return_value=[mock_attr])
        
        with patch.object(self.animator, 'get_facial_controls') as mock_get_controls:
            mock_get_controls.return_value = [mock_control]
            
            with patch.object(self.animator, 'undo_chunk_context') as mock_context:
                mock_context.__enter__ = Mock(return_value=self.animator)
                mock_context.__exit__ = Mock(return_value=None)
                
                # Should not raise an exception
                self.animator.reset_all_attributes()
                
                # Verify cutKey was called
                mock_pm.cutKey.assert_called_with(mock_control)


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
            TestMayaOperationsMocked
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
        loader = unittest.TestLoader()
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