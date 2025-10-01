"""
Facial Pose Animation Tool for Maya
===================================

A comprehensive tool for automating facial pose creation in Autodesk Maya for transfering to Unreal.
This script provides functionality to create, manage, and animate facial control poses.

Author: Nguyen Phi Hung
Date: September 30, 2025
"""

import os
import json
import pymel.core as pm
from typing import List, Dict, Tuple, Optional, Any, Union, Set
from enum import Enum
import logging
from contextlib import contextmanager
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ControlSelectionMode(Enum):
    """Enumeration for different control selection methods."""
    PATTERN = "pattern"
    SELECTION = "selection"
    OBJECT_SET = "object_set"
    METADATA = "metadata"


class FacialAnimatorError(Exception):
    """Base exception class for FacialPoseAnimator errors."""
    pass


class ControlSelectionError(FacialAnimatorError):
    """Exception raised when no valid controls can be found."""
    pass


class InvalidAttributeError(FacialAnimatorError):
    """Exception raised when attempting to work with invalid attributes."""
    pass


class DriverNodeError(FacialAnimatorError):
    """Exception raised when driver node operations fail."""
    pass


class FileOperationError(FacialAnimatorError):
    """Exception raised when file operations fail."""
    pass


class ObjectSetError(FacialAnimatorError):
    """Exception raised when object set operations fail."""
    pass


class PoseDataError(FacialAnimatorError):
    """Exception raised when pose data operations fail."""
    pass


@dataclass
class FacialPoseData:
    """
    Data class for storing facial pose information.
    
    Attributes:
        name: Human-readable name of the pose
        attribute_name: Attribute name for the facial driver node (sanitized for Maya)
        controls: Dictionary mapping control names to their attribute values
        description: Optional description of the pose
        timestamp: ISO format timestamp when pose was created
        maya_version: Maya version when pose was created
    """
    name: str
    attribute_name: str
    controls: Dict[str, Dict[str, float]]  # {control_name: {attr_name: value}}
    description: str = ""
    timestamp: str = ""
    maya_version: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose data to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FacialPoseData':
        """Create pose data from dictionary."""
        return cls(**data)
    
    def is_valid(self) -> bool:
        """Check if pose data is valid."""
        return bool(self.name and self.attribute_name and self.controls)
    
    def get_control_count(self) -> int:
        """Get the number of controls in this pose."""
        return len(self.controls)
    
    def get_attribute_count(self) -> int:
        """Get the total number of attributes across all controls."""
        return sum(len(attrs) for attrs in self.controls.values())
    
    def has_control(self, control_name: str) -> bool:
        """Check if pose contains a specific control."""
        return control_name in self.controls
    
    def get_control_attributes(self, control_name: str) -> Dict[str, float]:
        """Get attributes for a specific control."""
        return self.controls.get(control_name, {})
    
    def sanitize_attribute_name(self) -> str:
        """Return a Maya-safe attribute name."""
        # Replace spaces and special characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', self.attribute_name)
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = '_' + sanitized
        return sanitized or 'pose_attr'


class FacialPoseAnimator:
    """
    Main class for handling facial pose animation in Maya.
    
    This class provides methods to create, animate, and manage facial control poses
    with proper error handling and organized structure.
    """
    
    def __init__(self):
        """Initialize the FacialPoseAnimator with default settings."""
        self.last_key_time = 0
        self.facial_driver_node = "FacialPoseValue"
        self.control_pattern = "::*_CTRL"
        self.excluded_nodes = ["GUI", "pup"]
        self.excluded_attributes = ["scaleX", "scaleY", "scaleZ"]
        self.tolerance = 0.01
        
        # Default control selection settings
        self.default_selection_mode = ControlSelectionMode.PATTERN
        self.default_object_set = None
        
        # Metadata connection settings
        self.metadata_attr_name = "facialControlNodes"
        self.control_index_attr_prefix = "controlIndex_"
        
        # Undo/cleanup tracking
        self.created_nodes: Set[str] = set()
        self.created_connections: List[Tuple[str, str]] = []
        self.created_attributes: List[Tuple[str, str]] = []  # (node, attribute)
        self.enable_undo_tracking = True
        
        # Pose management settings
        self.saved_poses: Dict[str, FacialPoseData] = {}
        self.pose_storage_file: Optional[str] = None
        
        # Mapping for transform limit queries
        self.limit_type_map = {
            "translateX": lambda x: pm.transformLimits(x, tx=1, q=1),
            "translateY": lambda x: pm.transformLimits(x, ty=1, q=1),
            "translateZ": lambda x: pm.transformLimits(x, tz=1, q=1)
        }
    
    def _is_valid_control(self, control: pm.PyNode) -> bool:
        """
        Check if a control node is valid for processing.
        
        Args:
            control: PyMEL node to check
            
        Returns:
            bool: True if control is valid, False otherwise
        """
        node_name = control.nodeName()
        return not any(excluded in node_name for excluded in self.excluded_nodes)
    
    def _is_valid_attribute(self, attribute: pm.Attribute) -> bool:
        """
        Check if an attribute is valid for animation.
        
        Args:
            attribute: PyMEL attribute to check
            
        Returns:
            bool: True if attribute is valid, False otherwise
        """
        if (attribute.isLocked() or 
            attribute.isConnected() or 
            attribute.isHidden() or
            'double' not in attribute.get(type=True)):
            return False
            
        return attribute.longName() not in self.excluded_attributes
    
    def _get_attribute_range(self, control: pm.PyNode, attribute: pm.Attribute) -> List[float]:
        """
        Get the value range for an attribute.
        
        Args:
            control: The control node
            attribute: The attribute to get range for
            
        Returns:
            List[float]: List of values in the attribute's range
        """
        attr_name = attribute.longName()
        
        # Check if it's a transform attribute with limits
        for limit_attr, limit_func in self.limit_type_map.items():
            if limit_attr in attr_name:
                return limit_func(control)
        
        # Default to attribute's range
        return attribute.getRange()
    
    def _generate_pose_name(self, control: pm.PyNode, attribute: pm.Attribute, value: float) -> str:
        """
        Generate a standardized pose name.
        
        Args:
            control: The control node
            attribute: The attribute
            value: The attribute value
            
        Returns:
            str: Generated pose name
        """
        control_name = control.nodeName().split(':')[-1]
        attr_name = attribute.longName().replace('.', '_')
        value_str = str(value).replace(".", 'f').replace("-", "minus")
        
        return f"{control_name}_{attr_name}_{value_str}"
    
    def _create_metadata_connections(self, driver_node: pm.PyNode, control_nodes: List[pm.PyNode]) -> None:
        """
        Create metadata connections between driver node and facial control nodes.
        
        Args:
            driver_node: The facial pose driver node
            control_nodes: List of facial control nodes to connect
        """
        try:
            # Create main metadata attribute if it doesn't exist
            if not pm.attributeQuery(self.metadata_attr_name, node=driver_node, exists=True):
                pm.addAttr(driver_node, ln=self.metadata_attr_name, at='message', multi=True, indexMatters=True)
                self._track_created_attribute(driver_node, self.metadata_attr_name)
                logger.debug(f"Created metadata attribute: {driver_node}.{self.metadata_attr_name}")
            
            # Create individual control index attributes and connections
            for index, control in enumerate(control_nodes):
                control_index_attr = f"{self.control_index_attr_prefix}{index}"
                
                # Create control index attribute on driver node if it doesn't exist
                if not pm.attributeQuery(control_index_attr, node=driver_node, exists=True):
                    pm.addAttr(driver_node, ln=control_index_attr, at='message')
                    self._track_created_attribute(driver_node, control_index_attr)
                
                # Create reverse connection attribute on control node if it doesn't exist
                reverse_attr_name = f"facialDriver_{driver_node.nodeName().replace(':', '_')}"
                if not pm.attributeQuery(reverse_attr_name, node=control, exists=True):
                    pm.addAttr(control, ln=reverse_attr_name, at='message')
                    self._track_created_attribute(control, reverse_attr_name)
                
                # Create the metadata connections
                try:
                    # Connect control to driver's main metadata array
                    source_attr = f"{control}.message"
                    dest_attr = f"{driver_node}.{self.metadata_attr_name}[{index}]"
                    if not pm.isConnected(source_attr, dest_attr):
                        pm.connectAttr(source_attr, dest_attr)
                        self._track_created_connection(source_attr, dest_attr)
                        logger.debug(f"Connected metadata: {source_attr} -> {dest_attr}")
                    
                    # Connect control to driver's individual control index attribute
                    dest_attr = f"{driver_node}.{control_index_attr}"
                    if not pm.isConnected(source_attr, dest_attr):
                        pm.connectAttr(source_attr, dest_attr)
                        self._track_created_connection(source_attr, dest_attr)
                    
                    # Create reverse connection from driver to control
                    source_attr = f"{driver_node}.message"
                    dest_attr = f"{control}.{reverse_attr_name}"
                    if not pm.isConnected(source_attr, dest_attr):
                        pm.connectAttr(source_attr, dest_attr)
                        self._track_created_connection(source_attr, dest_attr)
                        
                except Exception as e:
                    logger.warning(f"Failed to create metadata connection for control {control}: {e}")
            
            logger.info(f"Created metadata connections for {len(control_nodes)} facial controls.")
            
        except Exception as e:
            logger.error(f"Error creating metadata connections: {e}")
    
    def _get_connected_facial_controls(self, driver_node: pm.PyNode) -> List[pm.PyNode]:
        """
        Get facial control nodes connected to the driver node via metadata.
        
        Args:
            driver_node: The facial pose driver node
            
        Returns:
            List[pm.PyNode]: List of connected facial control nodes
        """
        connected_controls = []
        
        try:
            # Check if metadata attribute exists
            if not pm.attributeQuery(self.metadata_attr_name, node=driver_node, exists=True):
                logger.debug(f"No metadata attribute found on {driver_node}")
                return connected_controls
            
            # Get connections from the metadata array attribute
            metadata_attr = driver_node.attr(self.metadata_attr_name)
            connections = metadata_attr.inputs()
            
            for connection in connections:
                try:
                    control_node = connection.node()
                    if isinstance(control_node, pm.nt.Transform):
                        connected_controls.append(control_node)
                except Exception as e:
                    logger.warning(f"Error processing metadata connection: {e}")
            
            logger.debug(f"Found {len(connected_controls)} controls connected via metadata.")
            return connected_controls
            
        except Exception as e:
            logger.error(f"Error getting connected facial controls: {e}")
            return connected_controls
    
    def _validate_metadata_connections(self, driver_node: pm.PyNode) -> Dict[str, Any]:
        """
        Validate the metadata connections for a driver node.
        
        Args:
            driver_node: The facial pose driver node
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            "has_metadata_attr": False,
            "connected_controls_count": 0,
            "broken_connections": [],
            "orphaned_attributes": []
        }
        
        try:
            # Check if main metadata attribute exists
            if pm.attributeQuery(self.metadata_attr_name, node=driver_node, exists=True):
                validation["has_metadata_attr"] = True
                
                # Get connected controls
                connected_controls = self._get_connected_facial_controls(driver_node)
                validation["connected_controls_count"] = len(connected_controls)
                
                # Check for broken reverse connections
                for control in connected_controls:
                    reverse_attr_name = f"facialDriver_{driver_node.nodeName().replace(':', '_')}"
                    if pm.attributeQuery(reverse_attr_name, node=control, exists=True):
                        reverse_attr = control.attr(reverse_attr_name)
                        if not reverse_attr.inputs():
                            validation["broken_connections"].append(f"{control}.{reverse_attr_name}")
                
                # Check for orphaned control index attributes
                for attr in driver_node.listAttr(userDefined=True):
                    if attr.attrName().startswith(self.control_index_attr_prefix):
                        if not attr.inputs():
                            validation["orphaned_attributes"].append(f"{driver_node}.{attr.attrName()}")
            
            logger.debug(f"Metadata validation completed for {driver_node}")
            return validation
            
        except Exception as e:
            logger.error(f"Error validating metadata connections: {e}")
            return validation
    
    def _cleanup_metadata_connections(self, driver_node: pm.PyNode) -> None:
        """
        Clean up broken or orphaned metadata connections.
        
        Args:
            driver_node: The facial pose driver node
        """
        try:
            validation = self._validate_metadata_connections(driver_node)
            
            # Remove orphaned control index attributes
            for orphaned_attr in validation["orphaned_attributes"]:
                try:
                    pm.deleteAttr(orphaned_attr)
                    logger.debug(f"Removed orphaned attribute: {orphaned_attr}")
                except Exception as e:
                    logger.warning(f"Failed to remove orphaned attribute {orphaned_attr}: {e}")
            
            # Clean up broken reverse connections
            for broken_connection in validation["broken_connections"]:
                try:
                    pm.deleteAttr(broken_connection)
                    logger.debug(f"Removed broken connection attribute: {broken_connection}")
                except Exception as e:
                    logger.warning(f"Failed to remove broken connection {broken_connection}: {e}")
            
            logger.info(f"Cleaned up metadata connections for {driver_node}")
            
        except Exception as e:
            logger.error(f"Error cleaning up metadata connections: {e}")
    
    def validate_scene_setup(self) -> Dict[str, bool]:
        """
        Validate the current Maya scene setup for facial animation.
        
        Returns:
            Dict[str, bool]: Dictionary of validation results
            
        Raises:
            FacialAnimatorError: If critical validation fails
        """
        validation_results = {
            "maya_available": True,
            "controls_found": False,
            "driver_node_exists": False,
            "scene_saved": False
        }
        
        try:
            # Check if PyMEL/Maya is available
            pm.ls()
        except Exception as e:
            validation_results["maya_available"] = False
            raise FacialAnimatorError(f"Maya/PyMEL not available: {e}") from e
        
        # Check if controls can be found
        try:
            controls = self.get_facial_controls()
            validation_results["controls_found"] = len(controls) > 0
        except ControlSelectionError:
            validation_results["controls_found"] = False
        
        # Check if driver node exists
        validation_results["driver_node_exists"] = bool(pm.ls(self.facial_driver_node))
        
        # Check if scene is saved
        try:
            scene_name = pm.sceneName()
            validation_results["scene_saved"] = bool(scene_name)
        except Exception:
            validation_results["scene_saved"] = False
        
        return validation_results
    
    def _track_created_node(self, node: Union[pm.PyNode, str]) -> None:
        """Track a node that was created during operations for potential cleanup."""
        if self.enable_undo_tracking:
            node_name = str(node)
            self.created_nodes.add(node_name)
            logger.debug(f"Tracking created node: {node_name}")
    
    def _track_created_connection(self, source_attr: str, dest_attr: str) -> None:
        """Track a connection that was created during operations for potential cleanup."""
        if self.enable_undo_tracking:
            self.created_connections.append((source_attr, dest_attr))
            logger.debug(f"Tracking created connection: {source_attr} -> {dest_attr}")
    
    def _track_created_attribute(self, node: Union[pm.PyNode, str], attr_name: str) -> None:
        """Track an attribute that was created during operations for potential cleanup."""
        if self.enable_undo_tracking:
            node_name = str(node)
            self.created_attributes.append((node_name, attr_name))
            logger.debug(f"Tracking created attribute: {node_name}.{attr_name}")
    
    def _cleanup_created_items(self) -> None:
        """Clean up all tracked nodes, connections, and attributes."""
        if not self.enable_undo_tracking:
            return
        
        cleanup_errors = []
        
        # Disconnect created connections
        for source_attr, dest_attr in reversed(self.created_connections):
            try:
                if pm.isConnected(source_attr, dest_attr):
                    pm.disconnectAttr(source_attr, dest_attr)
                    logger.debug(f"Disconnected: {source_attr} -> {dest_attr}")
            except Exception as e:
                cleanup_errors.append(f"Failed to disconnect {source_attr} -> {dest_attr}: {e}")
        
        # Remove created attributes
        for node_name, attr_name in reversed(self.created_attributes):
            try:
                if pm.objExists(node_name) and pm.attributeQuery(attr_name, node=node_name, exists=True):
                    pm.deleteAttr(f"{node_name}.{attr_name}")
                    logger.debug(f"Deleted attribute: {node_name}.{attr_name}")
            except Exception as e:
                cleanup_errors.append(f"Failed to delete attribute {node_name}.{attr_name}: {e}")
        
        # Delete created nodes
        for node_name in reversed(list(self.created_nodes)):
            try:
                if pm.objExists(node_name):
                    pm.delete(node_name)
                    logger.debug(f"Deleted node: {node_name}")
            except Exception as e:
                cleanup_errors.append(f"Failed to delete node {node_name}: {e}")
        
        # Clear tracking lists
        self.created_nodes.clear()
        self.created_connections.clear()
        self.created_attributes.clear()
        
        if cleanup_errors:
            logger.warning(f"Some cleanup operations failed: {'; '.join(cleanup_errors[:3])}")
        else:
            logger.info("Successfully cleaned up all created items.")
    
    def clear_undo_tracking(self) -> None:
        """Clear the undo tracking without performing cleanup."""
        self.created_nodes.clear()
        self.created_connections.clear()
        self.created_attributes.clear()
        logger.debug("Cleared undo tracking.")
    
    def set_undo_tracking(self, enabled: bool) -> None:
        """Enable or disable undo tracking for operations."""
        self.enable_undo_tracking = enabled
        if not enabled:
            self.clear_undo_tracking()
        logger.debug(f"Undo tracking {'enabled' if enabled else 'disabled'}.")
    
    @contextmanager
    def undo_chunk_context(self, chunk_name: str = "FacialPoseAnimator"):
        """
        Context manager for Maya undo chunks with automatic cleanup on failure.
        
        Args:
            chunk_name: Name for the undo chunk
        """
        # Clear previous tracking
        self.clear_undo_tracking()
        
        # Open undo chunk
        pm.undoInfo(openChunk=True, chunkName=chunk_name)
        
        try:
            yield self
            # If we get here, operation succeeded
            pm.undoInfo(closeChunk=True)
            logger.debug(f"Successfully completed undo chunk: {chunk_name}")
            
        except Exception as e:
            # Operation failed, perform cleanup
            logger.warning(f"Operation failed, performing cleanup for chunk: {chunk_name}")
            
            try:
                # Close the undo chunk first
                pm.undoInfo(closeChunk=True)
                
                # Perform our custom cleanup
                self._cleanup_created_items()
                
                # Then undo the Maya operations
                if pm.undoInfo(query=True, state=True):
                    pm.undo()
                    logger.info("Performed Maya undo after cleanup.")
                    
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
            
            # Re-raise the original exception
            raise e
        
        finally:
            # Always clear tracking at the end
            self.clear_undo_tracking()
    
    def set_default_selection_mode(self, mode: ControlSelectionMode, object_set_name: Optional[str] = None) -> None:
        """
        Set the default control selection mode for this animator instance.
        
        Args:
            mode: The default selection mode to use
            object_set_name: Default object set name (required if mode is OBJECT_SET)
        """
        self.default_selection_mode = mode
        if mode == ControlSelectionMode.OBJECT_SET and object_set_name:
            self.default_object_set = object_set_name
        logger.info(f"Default selection mode set to: {mode.value}")
    
    def create_facial_control_set(self, set_name: str, use_current_selection: bool = False) -> Optional[pm.PyNode]:
        """
        Create a Maya object set with facial controls.
        
        Args:
            set_name: Name for the new object set
            use_current_selection: If True, add current selection to set, otherwise use pattern matching
            
        Returns:
            pm.PyNode: The created object set, or None if creation failed
        """
        try:
            # Get controls to add to set
            if use_current_selection:
                controls = self._get_controls_from_selection()
            else:
                controls = self._get_controls_from_pattern()
            
            valid_controls = [ctrl for ctrl in controls if self._is_valid_control(ctrl)]
            
            if not valid_controls:
                raise ObjectSetError("No valid controls found to add to set.")
            
            # Create the set
            with self.undo_chunk_context("Create Facial Control Set"):
                try:
                    set_created = False
                    if pm.objExists(set_name):
                        logger.warning(f"Object set '{set_name}' already exists. Adding controls to existing set.")
                        control_set = pm.PyNode(set_name)
                    else:
                        control_set = pm.sets(name=set_name, empty=True)
                        self._track_created_node(control_set)
                        set_created = True
                    
                    # Add controls to set
                    pm.sets(control_set, add=valid_controls)
                    logger.info(f"Added {len(valid_controls)} controls to set '{set_name}'.")
                    
                    return control_set
                    
                except pm.MayaNodeError as e:
                    if set_created:
                        logger.warning("Object set creation failed, cleanup will remove the created set.")
                    raise ObjectSetError(f"Failed to create or modify object set '{set_name}': {e}") from e
            
        except (ControlSelectionError, ObjectSetError):
            raise  # Re-raise custom exceptions
        except Exception as e:
            raise ObjectSetError(f"Unexpected error creating facial control set '{set_name}': {e}") from e
    
    def get_facial_controls(self, 
                           mode: Optional[ControlSelectionMode] = None,
                           object_set_name: Optional[str] = None,
                           use_selection: bool = False) -> List[pm.PyNode]:
        """
        Get all valid facial controls using different selection methods.
        
        Args:
            mode: Selection mode (PATTERN, SELECTION, or OBJECT_SET)
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
        
        Returns:
            List[pm.PyNode]: List of valid facial control nodes
        """
        try:
            # Handle legacy parameter for backward compatibility
            if use_selection and mode is None:
                mode = ControlSelectionMode.SELECTION
            
            # Use default mode if none specified
            if mode is None:
                mode = self.default_selection_mode
            
            # Get controls based on selection mode
            try:
                if mode == ControlSelectionMode.SELECTION:
                    all_controls = self._get_controls_from_selection()
                elif mode == ControlSelectionMode.OBJECT_SET:
                    all_controls = self._get_controls_from_object_set(object_set_name)
                elif mode == ControlSelectionMode.METADATA:
                    all_controls = self._get_controls_from_metadata(object_set_name)  # object_set_name used as driver_node_name
                else:  # Default to PATTERN mode
                    all_controls = self._get_controls_from_pattern()
            except (ControlSelectionError, ObjectSetError, DriverNodeError) as e:
                # Try fallback to pattern matching for some modes
                if mode not in [ControlSelectionMode.PATTERN, ControlSelectionMode.METADATA]:
                    logger.warning(f"Primary selection method failed: {e}. Attempting fallback to pattern matching.")
                    try:
                        all_controls = self._get_controls_from_pattern()
                    except ControlSelectionError as fallback_error:
                        raise ControlSelectionError(f"Both primary and fallback selection methods failed. Primary: {e}, Fallback: {fallback_error}") from e
                else:
                    raise
            
            # Filter valid controls
            valid_controls = [ctrl for ctrl in all_controls if self._is_valid_control(ctrl)]
            
            if not valid_controls:
                raise ControlSelectionError(f"No valid facial controls found using {mode.value} mode. Check control naming patterns and exclusion rules.")
            
            logger.info(f"Found {len(valid_controls)} valid controls using {mode.value} mode.")
            return valid_controls
            
        except FacialAnimatorError:
            raise  # Re-raise custom exceptions
        except Exception as e:
            raise ControlSelectionError(f"Unexpected error getting facial controls: {e}") from e
    
    def _get_controls_from_selection(self) -> List[pm.PyNode]:
        """Get controls from current Maya selection."""
        try:
            selected_objects = pm.selected()
            if not selected_objects:
                raise ControlSelectionError("No objects are currently selected in Maya.")
            
            # Filter selection to only transform nodes
            controls = [obj for obj in selected_objects if isinstance(obj, pm.nt.Transform)]
            if not controls:
                raise ControlSelectionError("No transform nodes found in current selection.")
            
            logger.info(f"Using {len(controls)} selected transform objects.")
            return controls
        except pm.MayaNodeError as e:
            raise ControlSelectionError(f"Error accessing Maya selection: {e}") from e
    
    def _get_controls_from_pattern(self) -> List[pm.PyNode]:
        """Get controls using pattern matching."""
        try:
            controls = pm.ls(self.control_pattern, type='transform')
            if not controls:
                raise ControlSelectionError(f"No transform nodes found matching pattern '{self.control_pattern}'.")
            
            logger.info(f"Found {len(controls)} controls matching pattern '{self.control_pattern}'.")
            return controls
        except pm.MayaNodeError as e:
            raise ControlSelectionError(f"Error searching for controls with pattern '{self.control_pattern}': {e}") from e
    
    def _get_controls_from_object_set(self, object_set_name: Optional[str] = None) -> List[pm.PyNode]:
        """Get controls from Maya object set."""
        # Use provided name or default
        set_name = object_set_name or self.default_object_set
        
        if not set_name:
            raise ObjectSetError("No object set name provided and no default object set configured.")
        
        try:
            # Check if object set exists
            if not pm.objExists(set_name):
                raise ObjectSetError(f"Object set '{set_name}' does not exist in the scene.")
            
            # Get set members
            object_set = pm.PyNode(set_name)
            members = pm.sets(object_set, query=True) or []
            
            if not members:
                raise ObjectSetError(f"Object set '{set_name}' is empty.")
            
            # Filter to only transform nodes
            controls = [obj for obj in members if isinstance(obj, pm.nt.Transform)]
            if not controls:
                raise ObjectSetError(f"No transform nodes found in object set '{set_name}'.")
            
            logger.info(f"Found {len(controls)} transform objects in set '{set_name}'.")
            return controls
            
        except pm.MayaNodeError as e:
            raise ObjectSetError(f"Error accessing object set '{set_name}': {e}") from e
    
    def _get_controls_from_metadata(self, driver_node_name: Optional[str] = None) -> List[pm.PyNode]:
        """Get controls from driver node metadata connections."""
        # Use provided name or default
        node_name = driver_node_name or self.facial_driver_node
        
        try:
            # Check if driver node exists
            if not pm.objExists(node_name):
                raise DriverNodeError(f"Driver node '{node_name}' does not exist in the scene.")
            
            driver_node = pm.PyNode(node_name)
            controls = self._get_connected_facial_controls(driver_node)
            
            if not controls:
                raise DriverNodeError(f"No facial controls connected to driver node '{node_name}' via metadata.")
            
            logger.info(f"Found {len(controls)} controls connected to driver node '{node_name}' via metadata.")
            return controls
            
        except pm.MayaNodeError as e:
            raise DriverNodeError(f"Error accessing driver node '{node_name}': {e}") from e
    
    def reset_all_attributes(self, 
                            mode: Optional[ControlSelectionMode] = None,
                            object_set_name: Optional[str] = None,
                            use_selection: bool = False) -> None:
        """
        Reset all facial control attributes to zero and remove keyframes.
        
        Args:
            mode: Selection mode (PATTERN, SELECTION, or OBJECT_SET)
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
            
        Raises:
            ControlSelectionError: If no valid controls can be found
            InvalidAttributeError: If attribute operations fail
        """
        # Reset operations don't need undo tracking since they're cleaning up
        original_tracking = self.enable_undo_tracking
        self.set_undo_tracking(False)
        
        try:
            with self.undo_chunk_context("Reset Facial Attributes"):
                logger.info("Resetting all facial control attributes...")
                
                controls = self.get_facial_controls(mode=mode, object_set_name=object_set_name, use_selection=use_selection)
                
                reset_errors = []
                for control in controls:
                    try:
                        # Remove all keyframes from the control
                        pm.cutKey(control)
                        
                        # Reset keyable, visible attributes to zero
                        for attr in control.listAttr(k=True, v=True):
                            if self._is_valid_attribute(attr):
                                try:
                                    attr.set(0)
                                except (pm.MayaAttributeError, RuntimeError) as attr_error:
                                    reset_errors.append(f"Failed to reset {attr.longName()}: {attr_error}")
                                
                    except Exception as e:
                        reset_errors.append(f"Error resetting control {control}: {e}")
                
                if reset_errors and len(reset_errors) == len(controls):
                    # All controls failed to reset
                    raise InvalidAttributeError(f"Failed to reset all controls. Errors: {'; '.join(reset_errors[:3])}")
                elif reset_errors:
                    # Some controls failed, log warnings but continue
                    logger.warning(f"Some controls failed to reset: {'; '.join(reset_errors[:3])}")
                
                logger.info("Attribute reset completed.")
        
        finally:
            # Restore original tracking setting
            self.set_undo_tracking(original_tracking)
    
    def animate_facial_poses(self, 
                            output_file: Optional[str] = None,
                            mode: Optional[ControlSelectionMode] = None,
                            object_set_name: Optional[str] = None,
                            use_selection: bool = False) -> List[str]:
        """
        Create animation keyframes for all facial poses.
        
        Args:
            output_file: Optional path to write pose names
            mode: Selection mode (PATTERN, SELECTION, or OBJECT_SET)
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
            
        Returns:
            List[str]: List of generated pose names
            
        Raises:
            ControlSelectionError: If no valid controls found
            InvalidAttributeError: If animation fails
            FileOperationError: If output file cannot be written
        """
        with self.undo_chunk_context("Animate Facial Poses"):
            logger.info("Starting facial pose animation...")
            
            self.last_key_time = 0
            pose_names = []
            controls = self.get_facial_controls(mode=mode, object_set_name=object_set_name, use_selection=use_selection)
            
            animation_errors = []
            for control in controls:
                for attr in control.listAttr(k=True, v=True):
                    if not self._is_valid_attribute(attr):
                        continue
                    
                    try:
                        attr_range = self._get_attribute_range(control, attr)
                        control_poses = self._animate_attribute(attr, attr_range)
                        pose_names.extend(control_poses)
                        
                    except Exception as e:
                        animation_errors.append(f"Error animating attribute {attr}: {e}")
            
            if not pose_names:
                raise InvalidAttributeError("No poses were successfully animated.")
            
            if animation_errors:
                logger.warning(f"Some animations failed: {'; '.join(animation_errors[:3])}")
            
            # Write pose names to file if specified
            if output_file:
                self._write_pose_names(pose_names, output_file)
            
            logger.info(f"Animation completed. Generated {len(pose_names)} poses.")
            return pose_names
    
    def _animate_attribute(self, attribute: pm.Attribute, value_range: List[float]) -> List[str]:
        """
        Animate a single attribute through its value range.
        
        Args:
            attribute: The attribute to animate
            value_range: List of values to animate through
            
        Returns:
            List[str]: List of pose names created
            
        Raises:
            InvalidAttributeError: If attribute cannot be animated
        """
        if not self._is_valid_attribute(attribute):
            raise InvalidAttributeError(f"Attribute {attribute.longName()} is not valid for animation (locked, connected, or wrong type).")
        
        poses = []
        
        try:
            # Set initial keyframe at zero
            self.last_key_time -= 1
            attribute.set(0)
            pm.setKeyframe(attribute, time=self.last_key_time)
            
            # Animate through each value in range
            for value in value_range:
                if abs(value) < self.tolerance:  # Skip near-zero values
                    continue
                    
                self.last_key_time += 1
                attribute.set(value)
                pm.setKeyframe(attribute, time=self.last_key_time)
                
                pose_name = self._generate_pose_name(
                    attribute.node(), attribute, value
                )
                poses.append(pose_name)
            
            # Return to zero
            self.last_key_time += 1
            attribute.set(0)
            pm.setKeyframe(attribute, time=self.last_key_time)
            
            return poses
            
        except (pm.MayaAttributeError, RuntimeError) as e:
            raise InvalidAttributeError(f"Failed to animate attribute {attribute.longName()}: {e}") from e
    
    def create_facial_pose_driver(self, 
                                 mode: Optional[ControlSelectionMode] = None,
                                 object_set_name: Optional[str] = None,
                                 use_selection: bool = False) -> pm.PyNode:
        """
        Create a facial pose driver node with connected attributes.
        
        Args:
            mode: Selection mode (PATTERN, SELECTION, or OBJECT_SET)
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
        
        Returns:
            pm.PyNode: The created driver node
            
        Raises:
            DriverNodeError: If driver node creation fails
            ControlSelectionError: If no valid controls found
        """
        with self.undo_chunk_context("Create Facial Pose Driver"):
            logger.info("Creating facial pose driver...")
            
            # Create or get the driver node
            driver_node_created = False
            try:
                if not pm.ls(self.facial_driver_node):
                    driver_node = pm.createNode("transform", name=self.facial_driver_node)
                    self._track_created_node(driver_node)
                    driver_node_created = True
                else:
                    driver_node = pm.PyNode(self.facial_driver_node)
                    
            except Exception as e:
                raise DriverNodeError(f"Failed to create or access facial driver node '{self.facial_driver_node}': {e}") from e
            
            controls = self.get_facial_controls(mode=mode, object_set_name=object_set_name, use_selection=use_selection)
            pose_count = 0
            
            try:
                for control in controls:
                    for attr in control.listAttr(k=True, v=True):
                        if not self._is_valid_attribute(attr):
                            continue
                        
                        try:
                            attr_range = self._get_attribute_range(control, attr)
                            pose_count += self._create_driver_attributes(
                                driver_node, control, attr, attr_range
                            )
                            
                        except Exception as e:
                            logger.error(f"Error creating driver for {attr}: {e}")
                            # Continue with other attributes rather than failing completely
                
                if pose_count == 0:
                    raise DriverNodeError("No pose attributes were successfully created.")
                
                # Create metadata connections between driver and controls
                self._create_metadata_connections(driver_node, controls)
                
                logger.info(f"Driver creation completed. Created {pose_count} pose attributes with metadata connections.")
                return driver_node
                
            except Exception as e:
                # If we created the driver node and something failed, the cleanup will handle it
                if driver_node_created:
                    logger.warning("Driver node creation failed, cleanup will remove the created node.")
                raise
    
    def _create_driver_attributes(self, driver_node: pm.PyNode, control: pm.PyNode, 
                                attribute: pm.Attribute, value_range: List[float]) -> int:
        """
        Create driver attributes for a control attribute.
        
        Args:
            driver_node: The facial pose driver node
            control: The control node
            attribute: The attribute to create drivers for
            value_range: Range of values for the attribute
            
        Returns:
            int: Number of attributes created
        """
        created_count = 0
        
        for value in value_range:
            if abs(value) < self.tolerance or value is None:
                continue
            
            pose_name = self._generate_pose_name(control, attribute, value)
            
            # Skip if attribute already exists
            if hasattr(driver_node, pose_name):
                continue
            
            try:
                # Create driver attribute
                pm.addAttr(driver_node, ln=pose_name, at='float', k=1)
                self._track_created_attribute(driver_node, pose_name)
                
                # Create animation curve
                anim_curve = pm.createNode("animCurveUU", name=f"{pose_name}_driver")
                self._track_created_node(anim_curve)
                pm.setKeyframe(anim_curve, float=0, value=0)
                pm.setKeyframe(anim_curve, float=value, value=abs(value))
                
                # Connect the nodes
                source_attr = f"{attribute.node()}.{attribute.attrName()}"
                dest_attr = f"{anim_curve}.input"
                attribute >> anim_curve.input
                self._track_created_connection(source_attr, dest_attr)
                
                source_attr = f"{anim_curve}.output"
                dest_attr = f"{driver_node}.{pose_name}"
                anim_curve.output >> driver_node.attr(pose_name)
                self._track_created_connection(source_attr, dest_attr)
                
                created_count += 1
                
            except Exception as e:
                logger.warning(f"Error creating driver attribute {pose_name}: {e}")
        
        return created_count
    
    def connect_attributes_to_root(self, 
                                  root_node_name: str = "Root",
                                  mode: Optional[ControlSelectionMode] = None,
                                  object_set_name: Optional[str] = None,
                                  use_selection: bool = False) -> None:
        """
        Connect all facial control attributes to a root node.
        
        Args:
            root_node_name: Name of the root node to connect to
            mode: Selection mode (PATTERN, SELECTION, or OBJECT_SET)
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
            
        Raises:
            ControlSelectionError: If root node not found or no valid controls found
        """
        with self.undo_chunk_context("Connect Attributes to Root"):
            logger.info(f"Connecting attributes to root node: {root_node_name}")
            
            try:
                root_node = pm.PyNode(root_node_name)
            except pm.MayaNodeError as e:
                raise ControlSelectionError(f"Root node '{root_node_name}' not found in scene: {e}") from e
            
            controls = self.get_facial_controls(mode=mode, object_set_name=object_set_name, use_selection=use_selection)
            connection_count = 0
            connection_errors = []
            
            for control in controls:
                for attr in control.listAttr(k=True, v=True):
                    if not self._is_valid_attribute(attr):
                        continue
                    
                    try:
                        attr_name = f"{control.nodeName()}_{attr.longName().replace('.', '_')}"
                        
                        # Add attribute to root if it doesn't exist
                        attr_created = False
                        try:
                            if not pm.attributeQuery(attr_name, node=root_node, exists=True):
                                pm.addAttr(root_node, ln=attr_name, at='float', k=1)
                                self._track_created_attribute(root_node, attr_name)
                                attr_created = True
                        except RuntimeError:
                            pass  # Attribute already exists
                        
                        # Connect the attributes
                        source_attr = f"{attr.node()}.{attr.attrName()}"
                        dest_attr = f"{root_node}.{attr_name}"
                        attr >> root_node.attr(attr_name)
                        self._track_created_connection(source_attr, dest_attr)
                        connection_count += 1
                        
                    except Exception as e:
                        connection_errors.append(f"Error connecting attribute {attr}: {e}")
            
            if connection_count == 0:
                raise ControlSelectionError("No attributes were successfully connected to root node.")
            
            if connection_errors:
                logger.warning(f"Some connections failed: {'; '.join(connection_errors[:3])}")
            
            logger.info(f"Connected {connection_count} attributes to root node.")
    
    def animate_existing_poses(self, output_file: Optional[str] = None) -> List[str]:
        """
        Animate poses from existing facial driver node.
        
        Args:
            output_file: Optional path to write pose names
            
        Returns:
            List[str]: List of animated pose names
        """
        logger.info("Animating existing poses...")
        
        try:
            driver_nodes = pm.ls(f"::*{self.facial_driver_node}")
            if not driver_nodes:
                raise DriverNodeError(f"No driver node '{self.facial_driver_node}' found in scene.")
            
            driver_node = driver_nodes[0]
        except pm.MayaNodeError as e:
            raise DriverNodeError(f"Error accessing driver node '{self.facial_driver_node}': {e}") from e
        
        poses = []
        key_time = 1
        
        # Get all keyable attributes with inputs
        pose_attributes = [attr for attr in driver_node.listAttr(k=True) if attr.inputs()]
        
        for attr in pose_attributes:
            try:
                # Get the connected input attribute
                input_connections = attr.inputs()[0].inputs(p=True)
                if not input_connections:
                    continue
                
                input_attr = input_connections[0]
                
                if input_attr.isLocked():
                    continue
                
                # Extract value from attribute name
                value_str = attr.longName().split("_")[-1]
                value = float(value_str.replace("minus", "-").replace("f", "."))
                
                poses.append(attr.longName())
                
                # Animate the attribute
                self._animate_pose_attribute(input_attr, value, key_time)
                key_time += 1
                
            except Exception as e:
                logger.warning(f"Error animating pose {attr.longName()}: {e}")
        
        # Write pose names to file if specified
        if output_file:
            self._write_pose_names(poses, output_file)
        
        logger.info(f"Animated {len(poses)} existing poses.")
        return poses
    
    def _animate_pose_attribute(self, attribute: pm.Attribute, value: float, key_time: int) -> None:
        """
        Animate a single pose attribute.
        
        Args:
            attribute: The attribute to animate
            value: The target value
            key_time: The keyframe time
        """
        # Set initial state
        attribute.set(0)
        
        # Get existing keys or use default
        existing_keys = pm.keyframe(attribute, q=True)
        first_key = existing_keys[0] if existing_keys else key_time - 1
        
        # Set keyframes
        pm.setKeyframe(attribute, time=first_key)
        attribute.set(value)
        pm.setKeyframe(attribute, time=key_time)
        attribute.set(0)
        pm.setKeyframe(attribute, time=key_time + 1)
    
    def _write_pose_names(self, pose_names: List[str], output_file: str) -> None:
        """
        Write pose names to a file.
        
        Args:
            pose_names: List of pose names to write
            output_file: Path to the output file
            
        Raises:
            FileOperationError: If file cannot be written
        """
        if not pose_names:
            raise FileOperationError("Cannot write empty pose names list to file.")
        
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_file, "w") as f:
                f.writelines([f"\n{pose}" for pose in pose_names])
            
            logger.info(f"Pose names written to: {output_file}")
            
        except (OSError, IOError, PermissionError) as e:
            raise FileOperationError(f"Failed to write pose names to file '{output_file}': {e}") from e
    
    def get_default_output_path(self) -> str:
        """
        Get the default output path for pose names file.
        
        Returns:
            str: Default output file path
        """
        try:
            scene_path = pm.sceneName()
            if scene_path:
                return os.path.join(os.path.dirname(scene_path), "posename.txt")
            else:
                return os.path.join(os.getcwd(), "posename.txt")
        except Exception:
            return os.path.join(os.getcwd(), "posename.txt")
    
    def get_driver_metadata_info(self, driver_node_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about metadata connections for a driver node.
        
        Args:
            driver_node_name: Name of the driver node (uses default if None)
            
        Returns:
            Dict[str, Any]: Metadata information
        """
        node_name = driver_node_name or self.facial_driver_node
        
        metadata_info = {
            "driver_exists": False,
            "has_metadata": False,
            "connected_controls": [],
            "validation": {}
        }
        
        try:
            if pm.objExists(node_name):
                metadata_info["driver_exists"] = True
                driver_node = pm.PyNode(node_name)
                
                # Check for metadata attribute
                if pm.attributeQuery(self.metadata_attr_name, node=driver_node, exists=True):
                    metadata_info["has_metadata"] = True
                    
                    # Get connected controls
                    connected_controls = self._get_connected_facial_controls(driver_node)
                    metadata_info["connected_controls"] = [str(ctrl) for ctrl in connected_controls]
                    
                    # Get validation info
                    metadata_info["validation"] = self._validate_metadata_connections(driver_node)
            
            return metadata_info
            
        except Exception as e:
            logger.error(f"Error getting driver metadata info: {e}")
            return metadata_info
    
    def rebuild_metadata_connections(self, 
                                   driver_node_name: Optional[str] = None,
                                   mode: Optional[ControlSelectionMode] = None,
                                   object_set_name: Optional[str] = None,
                                   use_selection: bool = False) -> bool:
        """
        Rebuild metadata connections for an existing driver node.
        
        Args:
            driver_node_name: Name of the driver node (uses default if None)
            mode: Selection mode for finding controls
            object_set_name: Name of Maya object set to use (when mode is OBJECT_SET)
            use_selection: Legacy parameter for backward compatibility
            
        Returns:
            bool: True if successful, False otherwise
        """
        node_name = driver_node_name or self.facial_driver_node
        
        try:
            if not pm.objExists(node_name):
                logger.error(f"Driver node '{node_name}' does not exist.")
                return False
            
            driver_node = pm.PyNode(node_name)
            
            with self.undo_chunk_context("Rebuild Metadata Connections"):
                # Clean up existing metadata connections
                self._cleanup_metadata_connections(driver_node)
                
                # Get controls using specified method (excluding metadata mode to avoid recursion)
                if mode == ControlSelectionMode.METADATA:
                    mode = ControlSelectionMode.PATTERN
                
                controls = self.get_facial_controls(
                    mode=mode, 
                    object_set_name=object_set_name, 
                    use_selection=use_selection
                )
                
                # Create new metadata connections
                self._create_metadata_connections(driver_node, controls)
                
                logger.info(f"Successfully rebuilt metadata connections for {len(controls)} controls.")
                return True
                
        except Exception as e:
            logger.error(f"Error rebuilding metadata connections: {e}")
            return False
    
    def save_pose_from_selection(self, 
                                pose_name: str,
                                description: str = "",
                                use_current_selection: bool = True,
                                auto_save_to_file: bool = True,
                                output_directory: Optional[str] = None) -> FacialPoseData:
        """
        Save a pose from currently selected nodes or all valid controls.
        
        Args:
            pose_name: Human-readable name for the pose
            description: Optional description of the pose
            use_current_selection: If True, use selected nodes; if False, use all valid controls
            auto_save_to_file: If True, automatically save pose to JSON file
            output_directory: Directory to save pose file (uses default if None)
            
        Returns:
            FacialPoseData: The created pose data
            
        Raises:
            PoseDataError: If pose cannot be created
            ControlSelectionError: If no valid controls found
            FileOperationError: If auto-save fails
        """
        try:
            # Get controls to capture pose from
            if use_current_selection:
                controls = self._get_controls_from_selection()
            else:
                controls = self.get_facial_controls()
            
            if not controls:
                raise PoseDataError("No valid controls found to capture pose from.")
            
            # Filter to only valid controls
            valid_controls = [ctrl for ctrl in controls if self._is_valid_control(ctrl)]
            if not valid_controls:
                raise PoseDataError("No valid facial controls found in selection/scene.")
            
            # Capture current attribute values
            controls_data = {}
            captured_count = 0
            
            for control in valid_controls:
                control_name = control.nodeName()
                control_attrs = {}
                
                # Get all keyable, visible attributes
                for attr in control.listAttr(k=True, v=True):
                    if self._is_valid_attribute(attr):
                        try:
                            attr_name = attr.longName()
                            current_value = attr.get()
                            
                            # Only store non-zero values (with tolerance)
                            if abs(current_value) >= self.tolerance:
                                control_attrs[attr_name] = float(current_value)
                                captured_count += 1
                        except (pm.MayaAttributeError, RuntimeError, TypeError) as e:
                            logger.warning(f"Could not get value for {attr}: {e}")
                
                # Only add control if it has captured attributes
                if control_attrs:
                    controls_data[control_name] = control_attrs
            
            if not controls_data:
                raise PoseDataError("No non-zero attribute values found to capture in pose.")
            
            # Create pose data
            from datetime import datetime
            pose_data = FacialPoseData(
                name=pose_name,
                attribute_name=self._sanitize_pose_name_for_attr(pose_name),
                controls=controls_data,
                description=description,
                timestamp=datetime.now().isoformat(),
                maya_version=pm.about(version=True)
            )
            
            # Store in internal dictionary
            self.saved_poses[pose_name] = pose_data
            
            # Auto-save to file if requested
            if auto_save_to_file:
                try:
                    file_path = self._get_pose_file_path(pose_name, output_directory)
                    self._save_single_pose_to_file(pose_data, file_path)
                    logger.info(f"Auto-saved pose '{pose_name}' to: {file_path}")
                except Exception as e:
                    logger.warning(f"Auto-save failed for pose '{pose_name}': {e}")
                    # Don't raise exception here, just log warning
            
            logger.info(f"Saved pose '{pose_name}' with {len(controls_data)} controls and {captured_count} attributes.")
            return pose_data
            
        except (ControlSelectionError, PoseDataError):
            raise  # Re-raise custom exceptions
        except Exception as e:
            raise PoseDataError(f"Unexpected error saving pose '{pose_name}': {e}") from e
    
    def _sanitize_pose_name_for_attr(self, pose_name: str) -> str:
        """
        Sanitize pose name to be a valid Maya attribute name.
        
        Args:
            pose_name: Original pose name
            
        Returns:
            str: Sanitized attribute name
        """
        import re
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', pose_name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = 'pose_' + sanitized
        return sanitized or 'custom_pose'
    
    def _get_pose_file_path(self, pose_name: str, output_directory: Optional[str] = None) -> str:
        """
        Generate a file path for saving a single pose.
        
        Args:
            pose_name: Name of the pose
            output_directory: Directory to save in (uses default if None)
            
        Returns:
            str: Full file path for the pose
        """
        # Sanitize pose name for filename
        sanitized_name = self._sanitize_pose_name_for_filename(pose_name)
        filename = f"{sanitized_name}.json"
        
        # Determine output directory
        if output_directory is None:
            try:
                scene_path = pm.sceneName()
                if scene_path:
                    scene_dir = os.path.dirname(scene_path)
                    output_directory = os.path.join(scene_dir, "facial_poses")
                else:
                    output_directory = os.path.join(os.getcwd(), "facial_poses")
            except Exception:
                output_directory = os.path.join(os.getcwd(), "facial_poses")
        
        return os.path.join(output_directory, filename)
    
    def _sanitize_pose_name_for_filename(self, pose_name: str) -> str:
        """
        Sanitize pose name to be a valid filename.
        
        Args:
            pose_name: Original pose name
            
        Returns:
            str: Sanitized filename (without extension)
        """
        import re
        # Replace invalid filename characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', pose_name)
        # Replace spaces with underscores
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores and dots
        sanitized = sanitized.strip('_.')
        # Ensure it's not empty
        return sanitized or 'pose'
    
    def _save_single_pose_to_file(self, pose_data: FacialPoseData, file_path: str) -> None:
        """
        Save a single pose to a JSON file.
        
        Args:
            pose_data: The pose data to save
            file_path: Path to save the file
            
        Raises:
            FileOperationError: If file cannot be written
        """
        try:
            # Prepare single pose export data
            from datetime import datetime
            export_data = {
                'version': '1.0',
                'export_type': 'single_pose',
                'created_timestamp': datetime.now().isoformat(),
                'maya_version': pm.about(version=True),
                'facial_driver_node': self.facial_driver_node,
                'control_pattern': self.control_pattern,
                'pose': pose_data.to_dict()
            }
            
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
        except (OSError, IOError, PermissionError) as e:
            raise FileOperationError(f"Failed to save pose to file '{file_path}': {e}") from e
        except (ValueError, TypeError) as e:  # JSONEncodeError is a subclass of ValueError
            raise FileOperationError(f"Failed to serialize pose data: {e}") from e
    
    def apply_saved_pose(self, pose_name: str, blend_factor: float = 1.0) -> bool:
        """
        Apply a saved pose to the controls.
        
        Args:
            pose_name: Name of the saved pose to apply
            blend_factor: Blend factor (0.0 = no change, 1.0 = full pose)
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            PoseDataError: If pose cannot be applied
        """
        if pose_name not in self.saved_poses:
            raise PoseDataError(f"Pose '{pose_name}' not found in saved poses.")
        
        pose_data = self.saved_poses[pose_name]
        
        try:
            with self.undo_chunk_context(f"Apply Pose: {pose_name}"):
                applied_count = 0
                errors = []
                
                for control_name, attributes in pose_data.controls.items():
                    # Check if control exists in scene
                    if not pm.objExists(control_name):
                        errors.append(f"Control '{control_name}' not found in scene")
                        continue
                    
                    try:
                        control = pm.PyNode(control_name)
                        
                        for attr_name, target_value in attributes.items():
                            try:
                                # Check if attribute exists
                                if not pm.attributeQuery(attr_name, node=control, exists=True):
                                    errors.append(f"Attribute '{attr_name}' not found on {control_name}")
                                    continue
                                
                                attr = control.attr(attr_name)
                                
                                # Check if attribute is settable
                                if attr.isLocked() or attr.isConnected():
                                    errors.append(f"Attribute {control_name}.{attr_name} is locked or connected")
                                    continue
                                
                                # Apply blended value
                                if blend_factor >= 1.0:
                                    new_value = target_value
                                elif blend_factor <= 0.0:
                                    continue  # No change
                                else:
                                    current_value = attr.get()
                                    new_value = current_value + (target_value - current_value) * blend_factor
                                
                                attr.set(new_value)
                                applied_count += 1
                                
                            except (pm.MayaAttributeError, RuntimeError, TypeError) as e:
                                errors.append(f"Error setting {control_name}.{attr_name}: {e}")
                        
                    except pm.MayaNodeError as e:
                        errors.append(f"Error accessing control '{control_name}': {e}")
                
                if applied_count == 0:
                    raise PoseDataError(f"No attributes were successfully applied from pose '{pose_name}'. Errors: {'; '.join(errors[:3])}")
                
                if errors:
                    logger.warning(f"Some attributes failed to apply: {'; '.join(errors[:3])}")
                
                logger.info(f"Applied pose '{pose_name}' to {applied_count} attributes (blend: {blend_factor}).")
                return True
                
        except PoseDataError:
            raise
        except Exception as e:
            raise PoseDataError(f"Unexpected error applying pose '{pose_name}': {e}") from e
    
    def list_saved_poses(self) -> List[Dict[str, Any]]:
        """
        Get a list of all saved poses with their information.
        
        Returns:
            List[Dict[str, Any]]: List of pose information dictionaries
        """
        pose_list = []
        for pose_name, pose_data in self.saved_poses.items():
            pose_info = {
                'name': pose_name,
                'attribute_name': pose_data.attribute_name,
                'description': pose_data.description,
                'control_count': pose_data.get_control_count(),
                'attribute_count': pose_data.get_attribute_count(),
                'timestamp': pose_data.timestamp,
                'maya_version': pose_data.maya_version
            }
            pose_list.append(pose_info)
        
        return sorted(pose_list, key=lambda x: x['name'])
    
    def remove_saved_pose(self, pose_name: str) -> bool:
        """
        Remove a saved pose from memory.
        
        Args:
            pose_name: Name of the pose to remove
            
        Returns:
            bool: True if pose was removed, False if not found
        """
        if pose_name in self.saved_poses:
            del self.saved_poses[pose_name]
            logger.info(f"Removed pose '{pose_name}' from saved poses.")
            return True
        else:
            logger.warning(f"Pose '{pose_name}' not found in saved poses.")
            return False
    
    def export_poses_to_file(self, file_path: str, pose_names: Optional[List[str]] = None) -> None:
        """
        Export saved poses to a JSON file.
        
        Args:
            file_path: Path to save the poses file
            pose_names: Optional list of specific pose names to export (exports all if None)
            
        Raises:
            PoseDataError: If export fails
            FileOperationError: If file cannot be written
        """
        try:
            # Determine which poses to export
            if pose_names is None:
                poses_to_export = self.saved_poses
            else:
                poses_to_export = {name: self.saved_poses[name] for name in pose_names if name in self.saved_poses}
            
            if not poses_to_export:
                raise PoseDataError("No poses found to export.")
            
            # Prepare export data
            from datetime import datetime
            export_data = {
                'version': '1.0',
                'created_timestamp': datetime.now().isoformat(),
                'maya_version': pm.about(version=True),
                'facial_driver_node': self.facial_driver_node,
                'control_pattern': self.control_pattern,
                'poses': {name: pose.to_dict() for name, pose in poses_to_export.items()}
            }
            
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.pose_storage_file = file_path
            logger.info(f"Exported {len(poses_to_export)} poses to: {file_path}")
            
        except (OSError, IOError, PermissionError) as e:
            raise FileOperationError(f"Failed to write poses to file '{file_path}': {e}") from e
        except (ValueError, TypeError) as e:  # JSONEncodeError is a subclass of ValueError
            raise PoseDataError(f"Failed to serialize pose data: {e}") from e
        except Exception as e:
            raise PoseDataError(f"Unexpected error exporting poses: {e}") from e
    
    def import_poses_from_file(self, file_path: str, overwrite_existing: bool = False) -> List[str]:
        """
        Import poses from a JSON file.
        
        Args:
            file_path: Path to the poses file
            overwrite_existing: Whether to overwrite existing poses with same names
            
        Returns:
            List[str]: List of imported pose names
            
        Raises:
            PoseDataError: If import fails
            FileOperationError: If file cannot be read
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"Poses file not found: {file_path}")
            
            # Read and parse file
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate file format
            if 'poses' not in import_data:
                raise PoseDataError("Invalid poses file format: missing 'poses' key.")
            
            imported_names = []
            skipped_names = []
            
            for pose_name, pose_dict in import_data['poses'].items():
                try:
                    # Check for existing pose
                    if pose_name in self.saved_poses and not overwrite_existing:
                        skipped_names.append(pose_name)
                        continue
                    
                    # Create pose data object
                    pose_data = FacialPoseData.from_dict(pose_dict)
                    
                    # Validate pose data
                    if not pose_data.is_valid():
                        logger.warning(f"Skipping invalid pose data: {pose_name}")
                        continue
                    
                    # Store pose
                    self.saved_poses[pose_name] = pose_data
                    imported_names.append(pose_name)
                    
                except (KeyError, TypeError, ValueError) as e:
                    logger.warning(f"Error importing pose '{pose_name}': {e}")
            
            if not imported_names:
                raise PoseDataError("No valid poses were imported from the file.")
            
            self.pose_storage_file = file_path
            
            if skipped_names:
                logger.info(f"Skipped {len(skipped_names)} existing poses (use overwrite_existing=True to replace).")
            
            logger.info(f"Imported {len(imported_names)} poses from: {file_path}")
            return imported_names
            
        except (OSError, IOError, PermissionError) as e:
            raise FileOperationError(f"Failed to read poses file '{file_path}': {e}") from e
        except ValueError as e:  # JSONDecodeError is a subclass of ValueError
            raise PoseDataError(f"Invalid JSON format in poses file: {e}") from e
        except Exception as e:
            raise PoseDataError(f"Unexpected error importing poses: {e}") from e
    
    def load_single_pose_from_file(self, file_path: str, overwrite_existing: bool = False) -> Optional[str]:
        """
        Load a single pose from a JSON file.
        
        Args:
            file_path: Path to the single pose file
            overwrite_existing: Whether to overwrite existing pose with same name
            
        Returns:
            str or None: Name of loaded pose, or None if failed
            
        Raises:
            PoseDataError: If import fails
            FileOperationError: If file cannot be read
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"Pose file not found: {file_path}")
            
            # Read and parse file
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Check if it's a single pose file
            if 'pose' in import_data and 'export_type' in import_data:
                if import_data['export_type'] == 'single_pose':
                    # Handle single pose format
                    pose_dict = import_data['pose']
                    pose_name = pose_dict.get('name', 'Imported_Pose')
                    
                    # Check for existing pose
                    if pose_name in self.saved_poses and not overwrite_existing:
                        logger.warning(f"Pose '{pose_name}' already exists. Use overwrite_existing=True to replace.")
                        return None
                    
                    # Create pose data object
                    pose_data = FacialPoseData.from_dict(pose_dict)
                    
                    # Validate pose data
                    if not pose_data.is_valid():
                        raise PoseDataError(f"Invalid pose data in file: {file_path}")
                    
                    # Store pose
                    self.saved_poses[pose_name] = pose_data
                    
                    logger.info(f"Loaded single pose '{pose_name}' from: {file_path}")
                    return pose_name
                    
            # If not a single pose file, try regular import
            return self.import_poses_from_file(file_path, overwrite_existing)
            
        except (OSError, IOError, PermissionError) as e:
            raise FileOperationError(f"Failed to read pose file '{file_path}': {e}") from e
        except ValueError as e:  # JSONDecodeError is a subclass of ValueError
            raise PoseDataError(f"Invalid JSON format in pose file: {e}") from e
        except Exception as e:
            raise PoseDataError(f"Unexpected error loading pose: {e}") from e
    
    def create_pose_driver_attribute(self, pose_name: str) -> bool:
        """
        Create a driver attribute for a saved pose on the facial driver node.
        
        Args:
            pose_name: Name of the saved pose
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            PoseDataError: If pose or driver operations fail
            DriverNodeError: If driver node is not accessible
        """
        if pose_name not in self.saved_poses:
            raise PoseDataError(f"Pose '{pose_name}' not found in saved poses.")
        
        pose_data = self.saved_poses[pose_name]
        
        try:
            # Ensure driver node exists
            if not pm.ls(self.facial_driver_node):
                raise DriverNodeError(f"Facial driver node '{self.facial_driver_node}' does not exist. Create it first.")
            
            driver_node = pm.PyNode(self.facial_driver_node)
            attr_name = pose_data.sanitize_attribute_name()
            
            with self.undo_chunk_context(f"Create Pose Driver: {pose_name}"):
                # Check if attribute already exists
                if pm.attributeQuery(attr_name, node=driver_node, exists=True):
                    logger.warning(f"Attribute '{attr_name}' already exists on driver node.")
                    return False
                
                # Create the pose attribute
                pm.addAttr(driver_node, ln=attr_name, at='float', k=1, min=0, max=1, dv=0)
                self._track_created_attribute(driver_node, attr_name)
                
                # Create connections for pose application
                # This would typically involve set driven keys or custom nodes
                # For now, we'll just create the attribute
                
                logger.info(f"Created driver attribute '{attr_name}' for pose '{pose_name}'.")
                return True
                
        except pm.MayaNodeError as e:
            raise DriverNodeError(f"Error accessing driver node: {e}") from e
        except Exception as e:
            raise PoseDataError(f"Unexpected error creating driver attribute: {e}") from e
    
    def get_default_poses_file_path(self) -> str:
        """
        Get the default file path for saving/loading poses.
        
        Returns:
            str: Default poses file path
        """
        try:
            scene_path = pm.sceneName()
            if scene_path:
                scene_dir = os.path.dirname(scene_path)
                scene_name = os.path.splitext(os.path.basename(scene_path))[0]
                return os.path.join(scene_dir, f"{scene_name}_facial_poses.json")
            else:
                return os.path.join(os.getcwd(), "facial_poses.json")
        except Exception:
            return os.path.join(os.getcwd(), "facial_poses.json")
    
    def clear_all_saved_poses(self) -> None:
        """Clear all saved poses from memory."""
        pose_count = len(self.saved_poses)
        self.saved_poses.clear()
        logger.info(f"Cleared {pose_count} saved poses from memory.")
    
    def get_pose_comparison(self, pose1_name: str, pose2_name: str) -> Dict[str, Any]:
        """
        Compare two saved poses and return differences.
        
        Args:
            pose1_name: Name of first pose
            pose2_name: Name of second pose
            
        Returns:
            Dict[str, Any]: Comparison results
            
        Raises:
            PoseDataError: If poses not found
        """
        if pose1_name not in self.saved_poses:
            raise PoseDataError(f"Pose '{pose1_name}' not found.")
        if pose2_name not in self.saved_poses:
            raise PoseDataError(f"Pose '{pose2_name}' not found.")
        
        pose1 = self.saved_poses[pose1_name]
        pose2 = self.saved_poses[pose2_name]
        
        # Find common and unique controls
        controls1 = set(pose1.controls.keys())
        controls2 = set(pose2.controls.keys())
        
        common_controls = controls1.intersection(controls2)
        unique_to_pose1 = controls1 - controls2
        unique_to_pose2 = controls2 - controls1
        
        # Compare attribute values for common controls
        attribute_differences = {}
        for control in common_controls:
            attrs1 = set(pose1.controls[control].keys())
            attrs2 = set(pose2.controls[control].keys())
            
            common_attrs = attrs1.intersection(attrs2)
            control_diffs = {}
            
            for attr in common_attrs:
                val1 = pose1.controls[control][attr]
                val2 = pose2.controls[control][attr]
                if abs(val1 - val2) >= self.tolerance:
                    control_diffs[attr] = {'pose1': val1, 'pose2': val2, 'difference': val2 - val1}
            
            if control_diffs:
                attribute_differences[control] = control_diffs
        
        return {
            'pose1_name': pose1_name,
            'pose2_name': pose2_name,
            'common_controls': len(common_controls),
            'unique_to_pose1': len(unique_to_pose1),
            'unique_to_pose2': len(unique_to_pose2),
            'controls_unique_to_pose1': list(unique_to_pose1),
            'controls_unique_to_pose2': list(unique_to_pose2),
            'attribute_differences': attribute_differences,
            'total_differences': sum(len(diffs) for diffs in attribute_differences.values())
        }


# Convenience functions for backward compatibility and ease of use
def create_facial_animator() -> FacialPoseAnimator:
    """Create and return a FacialPoseAnimator instance."""
    return FacialPoseAnimator()


def quick_reset_facial_controls(mode: Optional[ControlSelectionMode] = None, 
                               object_set_name: Optional[str] = None,
                               use_selection: bool = False) -> bool:
    """
    Quick function to reset all facial controls.
    
    Returns:
        bool: True if reset was successful, False otherwise
    
    Raises:
        ControlSelectionError: If no valid controls can be found
        InvalidAttributeError: If attribute operations fail
    """
    try:
        animator = FacialPoseAnimator()
        animator.reset_all_attributes(mode=mode, object_set_name=object_set_name, use_selection=use_selection)
        return True
    except Exception:
        return False


def quick_animate_facial_poses(output_file: Optional[str] = None, 
                              mode: Optional[ControlSelectionMode] = None,
                              object_set_name: Optional[str] = None,
                              use_selection: bool = False):
    """Quick function to animate facial poses."""
    animator = FacialPoseAnimator()
    default_output = animator.get_default_output_path() if output_file is None else output_file
    return animator.animate_facial_poses(default_output, mode=mode, object_set_name=object_set_name, use_selection=use_selection)


def quick_create_pose_driver(mode: Optional[ControlSelectionMode] = None,
                            object_set_name: Optional[str] = None,
                            use_selection: bool = False):
    """Quick function to create facial pose driver."""
    animator = FacialPoseAnimator()
    return animator.create_facial_pose_driver(mode=mode, object_set_name=object_set_name, use_selection=use_selection)


def quick_animate_existing_poses(output_file: Optional[str] = None):
    """Quick function to animate existing poses."""
    animator = FacialPoseAnimator()
    default_output = animator.get_default_output_path() if output_file is None else output_file
    return animator.animate_existing_poses(default_output)


def create_facial_control_set_from_selection(set_name: str = "FacialControls_Set"):
    """
    Quick function to create an object set from current selection.
    
    Raises:
        ControlSelectionError: If no valid objects are selected
        ObjectSetError: If set creation fails
    """
    animator = FacialPoseAnimator()
    return animator.create_facial_control_set(set_name, use_current_selection=True)


def create_facial_control_set_from_pattern(set_name: str = "FacialControls_Set"):
    """
    Quick function to create an object set from pattern matching.
    
    Raises:
        ControlSelectionError: If no controls match the pattern
        ObjectSetError: If set creation fails
    """
    animator = FacialPoseAnimator()
    return animator.create_facial_control_set(set_name, use_current_selection=False)


def quick_animate_from_set(set_name: str, output_file: Optional[str] = None):
    """
    Quick function to animate poses using controls from an object set.
    
    Raises:
        ObjectSetError: If object set doesn't exist or is empty
        ControlSelectionError: If no valid controls found in set
        InvalidAttributeError: If animation fails
        FileOperationError: If output file cannot be written
    """
    animator = FacialPoseAnimator()
    default_output = animator.get_default_output_path() if output_file is None else output_file
    return animator.animate_facial_poses(
        output_file=default_output,
        mode=ControlSelectionMode.OBJECT_SET,
        object_set_name=set_name
    )


def safe_create_pose_driver(mode: Optional[ControlSelectionMode] = None,
                           object_set_name: Optional[str] = None,
                           use_selection: bool = False) -> Optional[pm.PyNode]:
    """
    Safely create facial pose driver with automatic cleanup on failure.
    
    Returns:
        pm.PyNode or None: The created driver node, or None if creation failed
    """
    try:
        animator = FacialPoseAnimator()
        return animator.create_facial_pose_driver(
            mode=mode,
            object_set_name=object_set_name,
            use_selection=use_selection
        )
    except FacialAnimatorError as e:
        logger.error(f"Failed to create pose driver: {e}")
        return None


def safe_connect_to_root(root_node_name: str = "Root",
                        mode: Optional[ControlSelectionMode] = None,
                        object_set_name: Optional[str] = None,
                        use_selection: bool = False) -> bool:
    """
    Safely connect attributes to root with automatic cleanup on failure.
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        animator = FacialPoseAnimator()
        animator.connect_attributes_to_root(
            root_node_name=root_node_name,
            mode=mode,
            object_set_name=object_set_name,
            use_selection=use_selection
        )
        return True
    except FacialAnimatorError as e:
        logger.error(f"Failed to connect attributes to root: {e}")
        return False


def get_driver_metadata_info(driver_node_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to get metadata information about a driver node.
    
    Args:
        driver_node_name: Name of the driver node
        
    Returns:
        Dict[str, Any]: Metadata information
    """
    animator = FacialPoseAnimator()
    return animator.get_driver_metadata_info(driver_node_name)


def rebuild_driver_metadata(driver_node_name: Optional[str] = None,
                           mode: Optional[ControlSelectionMode] = None) -> bool:
    """
    Quick function to rebuild metadata connections for a driver node.
    
    Args:
        driver_node_name: Name of the driver node
        mode: Selection mode for finding controls
        
    Returns:
        bool: True if successful, False otherwise
    """
    animator = FacialPoseAnimator()
    return animator.rebuild_metadata_connections(driver_node_name, mode)


# Pose Management Convenience Functions

def save_pose_from_selection(pose_name: str, 
                           description: str = "", 
                           auto_save_to_file: bool = True,
                           output_directory: Optional[str] = None) -> Optional[FacialPoseData]:
    """
    Quick function to save a pose from current selection with auto-save to file.
    
    Args:
        pose_name: Name for the pose
        description: Optional description
        auto_save_to_file: Whether to automatically save to JSON file
        output_directory: Directory to save pose file (uses default if None)
        
    Returns:
        FacialPoseData or None: The saved pose data, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        return animator.save_pose_from_selection(
            pose_name, 
            description, 
            use_current_selection=True,
            auto_save_to_file=auto_save_to_file,
            output_directory=output_directory
        )
    except FacialAnimatorError as e:
        logger.error(f"Failed to save pose from selection: {e}")
        return None


def save_pose_from_all_controls(pose_name: str, 
                              description: str = "", 
                              auto_save_to_file: bool = True,
                              output_directory: Optional[str] = None) -> Optional[FacialPoseData]:
    """
    Quick function to save a pose from all valid facial controls with auto-save to file.
    
    Args:
        pose_name: Name for the pose
        description: Optional description
        auto_save_to_file: Whether to automatically save to JSON file
        output_directory: Directory to save pose file (uses default if None)
        
    Returns:
        FacialPoseData or None: The saved pose data, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        return animator.save_pose_from_selection(
            pose_name, 
            description, 
            use_current_selection=False,
            auto_save_to_file=auto_save_to_file,
            output_directory=output_directory
        )
    except FacialAnimatorError as e:
        logger.error(f"Failed to save pose from all controls: {e}")
        return None


def apply_saved_pose(pose_name: str, blend_factor: float = 1.0) -> bool:
    """
    Quick function to apply a saved pose.
    
    Args:
        pose_name: Name of the saved pose
        blend_factor: Blend factor (0.0 to 1.0)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        animator = FacialPoseAnimator()
        return animator.apply_saved_pose(pose_name, blend_factor)
    except FacialAnimatorError as e:
        logger.error(f"Failed to apply pose '{pose_name}': {e}")
        return False


def list_saved_poses() -> List[Dict[str, Any]]:
    """
    Quick function to list all saved poses.
    
    Returns:
        List[Dict[str, Any]]: List of pose information
    """
    animator = FacialPoseAnimator()
    return animator.list_saved_poses()


def export_poses_to_file(file_path: Optional[str] = None, pose_names: Optional[List[str]] = None) -> bool:
    """
    Quick function to export poses to file.
    
    Args:
        file_path: Path to save file (uses default if None)
        pose_names: Specific poses to export (exports all if None)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        animator = FacialPoseAnimator()
        output_path = file_path or animator.get_default_poses_file_path()
        animator.export_poses_to_file(output_path, pose_names)
        return True
    except FacialAnimatorError as e:
        logger.error(f"Failed to export poses: {e}")
        return False


def import_poses_from_file(file_path: Optional[str] = None, overwrite_existing: bool = False) -> Optional[List[str]]:
    """
    Quick function to import poses from file.
    
    Args:
        file_path: Path to poses file (uses default if None)
        overwrite_existing: Whether to overwrite existing poses
        
    Returns:
        List[str] or None: List of imported pose names, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        input_path = file_path or animator.get_default_poses_file_path()
        return animator.import_poses_from_file(input_path, overwrite_existing)
    except FacialAnimatorError as e:
        logger.error(f"Failed to import poses: {e}")
        return None


def load_single_pose_from_file(file_path: str, overwrite_existing: bool = False) -> Optional[str]:
    """
    Quick function to load a single pose from file.
    
    Args:
        file_path: Path to the single pose file
        overwrite_existing: Whether to overwrite existing pose
        
    Returns:
        str or None: Name of loaded pose, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        return animator.load_single_pose_from_file(file_path, overwrite_existing)
    except FacialAnimatorError as e:
        logger.error(f"Failed to load single pose: {e}")
        return None


def create_pose_driver_from_saved_poses(pose_names: Optional[List[str]] = None) -> bool:
    """
    Quick function to create driver attributes for saved poses.
    
    Args:
        pose_names: Specific poses to create drivers for (all if None)
        
    Returns:
        bool: True if any drivers were created successfully
    """
    try:
        animator = FacialPoseAnimator()
        
        # Get pose names to process
        if pose_names is None:
            pose_names = list(animator.saved_poses.keys())
        
        if not pose_names:
            logger.warning("No saved poses found to create drivers for.")
            return False
        
        success_count = 0
        for pose_name in pose_names:
            try:
                if animator.create_pose_driver_attribute(pose_name):
                    success_count += 1
            except FacialAnimatorError as e:
                logger.warning(f"Failed to create driver for pose '{pose_name}': {e}")
        
        logger.info(f"Created drivers for {success_count}/{len(pose_names)} poses.")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Failed to create pose drivers: {e}")
        return False


def compare_saved_poses(pose1_name: str, pose2_name: str) -> Optional[Dict[str, Any]]:
    """
    Quick function to compare two saved poses.
    
    Args:
        pose1_name: Name of first pose
        pose2_name: Name of second pose
        
    Returns:
        Dict[str, Any] or None: Comparison results, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        return animator.get_pose_comparison(pose1_name, pose2_name)
    except FacialAnimatorError as e:
        logger.error(f"Failed to compare poses: {e}")
        return None


def save_and_export_pose(pose_name: str, 
                        description: str = "",
                        use_current_selection: bool = True,
                        export_file: Optional[str] = None,
                        auto_save_individual: bool = True,
                        output_directory: Optional[str] = None) -> bool:
    """
    Convenience function to save a pose with auto-save and optional collection export.
    
    Args:
        pose_name: Name for the pose
        description: Optional description
        use_current_selection: Use selected nodes vs all controls
        export_file: File to export collection to (optional, uses default if None)
        auto_save_individual: Whether to auto-save individual pose file
        output_directory: Directory for individual pose files
        
    Returns:
        bool: True if save succeeded
    """
    try:
        animator = FacialPoseAnimator()
        
        # Save the pose with auto-save
        pose_data = animator.save_pose_from_selection(
            pose_name, 
            description, 
            use_current_selection,
            auto_save_to_file=auto_save_individual,
            output_directory=output_directory
        )
        if not pose_data:
            return False
        
        # Optionally also export to collection file
        if export_file:
            try:
                animator.export_poses_to_file(export_file, [pose_name])
                logger.info(f"Also exported pose '{pose_name}' to collection: {export_file}")
            except Exception as e:
                logger.warning(f"Collection export failed: {e}")
        
        return True
        
    except FacialAnimatorError as e:
        logger.error(f"Failed to save pose '{pose_name}': {e}")
        return False


def quick_pose_workflow_from_selection(pose_name: str, 
                                     description: str = "", 
                                     create_driver: bool = True,
                                     auto_save_individual: bool = True,
                                     export_to_collection: bool = True,
                                     output_directory: Optional[str] = None) -> bool:
    """
    Complete workflow: save pose from selection with auto-save, create driver attribute, and optional collection export.
    
    Args:
        pose_name: Name for the pose
        description: Optional description
        create_driver: Whether to create driver attribute
        auto_save_individual: Whether to auto-save individual pose file
        export_to_collection: Whether to also export to collection file
        output_directory: Directory for individual pose files
        
    Returns:
        bool: True if workflow completed successfully
    """
    try:
        animator = FacialPoseAnimator()
        
        # Save pose from selection with auto-save
        pose_data = animator.save_pose_from_selection(
            pose_name, 
            description, 
            use_current_selection=True,
            auto_save_to_file=auto_save_individual,
            output_directory=output_directory
        )
        if not pose_data:
            return False
        
        # Create driver attribute if requested
        if create_driver:
            try:
                animator.create_pose_driver_attribute(pose_name)
            except FacialAnimatorError as e:
                logger.warning(f"Could not create driver attribute: {e}")
        
        # Export to collection file if requested
        if export_to_collection:
            try:
                animator.export_poses_to_file(animator.get_default_poses_file_path(), [pose_name])
            except Exception as e:
                logger.warning(f"Collection export failed: {e}")
        
        logger.info(f"Completed pose workflow for '{pose_name}'.")
        return True
        
    except FacialAnimatorError as e:
        logger.error(f"Failed pose workflow for '{pose_name}': {e}")
        return False


def quick_animate_from_metadata(driver_node_name: Optional[str] = None,
                               output_file: Optional[str] = None) -> Optional[List[str]]:
    """
    Quick function to animate poses using controls from driver metadata.
    
    Args:
        driver_node_name: Name of the driver node (uses default if None)
        output_file: Optional path to write pose names
        
    Returns:
        List[str] or None: List of pose names, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        default_output = animator.get_default_output_path() if output_file is None else output_file
        return animator.animate_facial_poses(
            output_file=default_output,
            mode=ControlSelectionMode.METADATA,
            object_set_name=driver_node_name
        )
    except FacialAnimatorError as e:
        logger.error(f"Failed to animate from metadata: {e}")
        return None


def quick_save_pose_to_named_file(pose_name: str, 
                                description: str = "",
                                use_current_selection: bool = True,
                                output_directory: Optional[str] = None) -> Optional[str]:
    """
    Quick function to save pose directly to a named JSON file.
    
    Args:
        pose_name: Name for the pose (used for both pose name and filename)
        description: Optional description
        use_current_selection: Use selected nodes vs all controls
        output_directory: Directory to save pose file
        
    Returns:
        str or None: Path to saved file, or None if failed
    """
    try:
        animator = FacialPoseAnimator()
        
        # Save pose with auto-save enabled
        pose_data = animator.save_pose_from_selection(
            pose_name, 
            description, 
            use_current_selection=use_current_selection,
            auto_save_to_file=True,
            output_directory=output_directory
        )
        
        if pose_data:
            file_path = animator._get_pose_file_path(pose_name, output_directory)
            return file_path
        
        return None
        
    except FacialAnimatorError as e:
        logger.error(f"Failed to save pose to named file: {e}")
        return None


def batch_save_poses_from_selection_states(pose_definitions: List[Tuple[str, str]], 
                                          output_directory: Optional[str] = None) -> List[str]:
    """
    Save multiple poses by manually setting controls for each pose definition.
    
    Args:
        pose_definitions: List of (pose_name, description) tuples
        output_directory: Directory to save pose files
        
    Returns:
        List[str]: List of successfully saved pose file paths
        
    Note:
        This function expects the user to manually set up controls for each pose
        and press continue when ready to capture each pose.
    """
    saved_files = []
    
    try:
        animator = FacialPoseAnimator()
        
        for pose_name, description in pose_definitions:
            try:
                # In a real implementation, you might want to add user interaction here
                # For now, we'll just capture the current state
                
                pose_data = animator.save_pose_from_selection(
                    pose_name,
                    description,
                    use_current_selection=True,
                    auto_save_to_file=True,
                    output_directory=output_directory
                )
                
                if pose_data:
                    file_path = animator._get_pose_file_path(pose_name, output_directory)
                    saved_files.append(file_path)
                    logger.info(f"Saved pose '{pose_name}' to: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to save pose '{pose_name}': {e}")
        
        return saved_files
        
    except Exception as e:
        logger.error(f"Batch save operation failed: {e}")
        return saved_files


def get_pose_files_in_directory(directory: Optional[str] = None) -> List[str]:
    """
    Get list of pose JSON files in a directory.
    
    Args:
        directory: Directory to search (uses default if None)
        
    Returns:
        List[str]: List of pose file paths
    """
    try:
        animator = FacialPoseAnimator()
        
        if directory is None:
            # Use default pose directory
            directory = animator._get_pose_file_path("dummy", None)
            directory = os.path.dirname(directory)
        
        if not os.path.exists(directory):
            return []
        
        pose_files = []
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                try:
                    # Quick validation that it's a pose file
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if 'pose' in data or 'poses' in data:
                            pose_files.append(file_path)
                except:
                    continue  # Skip invalid files
        
        return sorted(pose_files)
        
    except Exception as e:
        logger.error(f"Error getting pose files: {e}")
        return []


def load_all_poses_from_directory(directory: Optional[str] = None, 
                                 overwrite_existing: bool = False) -> List[str]:
    """
    Load all pose files from a directory.
    
    Args:
        directory: Directory to load from (uses default if None)
        overwrite_existing: Whether to overwrite existing poses
        
    Returns:
        List[str]: List of loaded pose names
    """
    try:
        pose_files = get_pose_files_in_directory(directory)
        loaded_poses = []
        
        animator = FacialPoseAnimator()
        
        for file_path in pose_files:
            try:
                result = animator.load_single_pose_from_file(file_path, overwrite_existing)
                if isinstance(result, str):
                    loaded_poses.append(result)
                elif isinstance(result, list):
                    loaded_poses.extend(result)
            except Exception as e:
                logger.warning(f"Failed to load pose from {file_path}: {e}")
        
        logger.info(f"Loaded {len(loaded_poses)} poses from directory: {directory}")
        return loaded_poses
        
    except Exception as e:
        logger.error(f"Failed to load poses from directory: {e}")
        return []


# Example Main execution (equivalent to the original script's bottom section)
# if __name__ == "__main__":
    # Create animator instance
    # facial_animator = create_facial_animator()
    
    # Traditional animation workflow:
    # facial_animator.reset_all_attributes()
    # facial_animator.animate_facial_poses()
    # facial_animator.create_facial_pose_driver()
    # facial_animator.animate_existing_poses()
    
    # New pose saving workflow examples with auto-save:
    
    # Save a pose from currently selected controls with auto-save to individual JSON file
    # pose_data = facial_animator.save_pose_from_selection("Happy_Smile", "A happy smiling expression")
    # This automatically creates: facial_poses/Happy_Smile.json
    
    # Save pose without auto-save (old behavior)
    # pose_data = facial_animator.save_pose_from_selection("Happy_Smile", "A happy smiling expression", 
    #                                                     auto_save_to_file=False)
    
    # Save pose to custom directory
    # pose_data = facial_animator.save_pose_from_selection("Happy_Smile", "A happy smiling expression",
    #                                                     output_directory="C:/MyProject/Poses")
    
    # Apply a saved pose with full strength
    # facial_animator.apply_saved_pose("Happy_Smile", blend_factor=1.0)
    
    # Apply a pose at 50% strength
    # facial_animator.apply_saved_pose("Happy_Smile", blend_factor=0.5)
    
    # List all saved poses
    # pose_list = facial_animator.list_saved_poses()
    # for pose_info in pose_list:
    #     print(f"Pose: {pose_info['name']}, Controls: {pose_info['control_count']}")
    
    # Export poses to file
    # facial_animator.export_poses_to_file("my_facial_poses.json")
    
    # Import poses from file
    # imported_poses = facial_animator.import_poses_from_file("my_facial_poses.json")
    
    # Create driver attributes for saved poses
    # facial_animator.create_pose_driver_attribute("Happy_Smile")
    
    # Compare two poses
    # comparison = facial_animator.get_pose_comparison("Happy_Smile", "Sad_Frown")
    
    # Quick convenience functions with auto-save:
    
    # Save pose from selection with auto-save to individual file
    # save_pose_from_selection("Surprised", "Wide-eyed surprise expression")
    # Creates: facial_poses/Surprised.json
    
    # Save pose to custom directory
    # save_pose_from_selection("Surprised", "Wide-eyed surprise", 
    #                         output_directory="C:/MyProject/CharacterPoses")
    
    # Complete workflow with auto-save individual file
    # quick_pose_workflow_from_selection("Angry", "Angry expression with furrowed brow", 
    #                                   create_driver=True, auto_save_individual=True)
    
    # Save pose directly to named file
    # file_path = quick_save_pose_to_named_file("Custom_Expression", "My custom expression")
    
    # Load a single pose from file
    # pose_name = load_single_pose_from_file("facial_poses/Happy_Smile.json")
    
    # Load all poses from directory
    # loaded_poses = load_all_poses_from_directory("C:/MyProject/Poses")
    
    # Apply an existing pose
    # apply_saved_pose("Happy_Smile", blend_factor=0.75)