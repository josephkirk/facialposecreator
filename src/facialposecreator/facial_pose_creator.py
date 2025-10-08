"""
Facial Pose Creator UI
======================

A user interface for the Facial Pose Animation Tool for Maya.
Provides a comprehensive GUI for creating, managing, and animating facial control poses.

Author: Nguyen Phi Hung
Date: October 1, 2025
Updated: October 7, 2025 - Migrated to use new unified API with improved error handling

Changes (October 7, 2025):
- Imported new unified API functions (safe_animate_poses, safe_create_driver, safe_save_pose, safe_load_poses)
- Imported exception classes for proper error handling (FacialAnimatorError and subclasses)
- Updated animate_facial_poses_handler() to use safe_animate_poses with specific exception handling
- Updated save_pose() to use safe_save_pose with specific exception handling
- Updated create_driver() to use safe_create_driver with specific exception handling
- Updated load_poses_from_file() to use safe_load_poses
- All UI operations now use "safe" variants that return None on error instead of raising exceptions
- Improved error messages with specific exception types (ControlSelectionError, DriverNodeError, etc.)
"""

import sys
from typing import Dict, Any

# Try to import PySide6, fallback to PySide2
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
        QDoubleSpinBox, QCheckBox, QGroupBox, QListWidget, QListWidgetItem,
        QFileDialog, QMessageBox, QTabWidget, QProgressBar, QSplitter,
        QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox
    )
    from PySide6.QtCore import Qt, Signal, QTimer, QSize
    from PySide6.QtGui import QIcon, QFont, QColor
    PYSIDE_VERSION = 6
    print("Using PySide6")
except ImportError:
    try:
        from PySide2.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
            QDoubleSpinBox, QCheckBox, QGroupBox, QListWidget, QListWidgetItem,
            QFileDialog, QMessageBox, QTabWidget, QProgressBar, QSplitter,
            QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox
        )
        from PySide2.QtCore import Qt, Signal, QTimer, QSize
        from PySide2.QtGui import QIcon, QFont, QColor
        PYSIDE_VERSION = 2
        print("Using PySide2")
    except ImportError:
        raise ImportError("Neither PySide6 nor PySide2 is available. Please install one of them.")

# Import the facial pose animator module
try:
    from . import facial_pose_animator
    # Import the new unified API functions
    from .facial_pose_animator import (
        # Version constant
        __version__,
        # Exception classes for proper error handling
        FacialAnimatorError,
        ControlSelectionError,
        DriverNodeError,
        InvalidAttributeError,
        FileOperationError,
        ObjectSetError,
        PoseDataError,
        # Enums for selection modes
        ControlSelectionMode,
        # New unified convenience functions (safe variants for UI)
        safe_animate_poses,
        safe_create_driver,
        safe_register_control_to_driver,
        safe_register_selected_control_to_driver,
        safe_save_pose,
        safe_load_poses,
    )
    # Additional check: verify we're actually in Maya
    try:
        import maya.cmds as cmds
        # Check if Maya is actually running (not just imported)
        cmds.about(version=True)
        MAYA_AVAILABLE = True
        print("facial_pose_animator module imported successfully - Maya detected")
        print("Imported new unified API functions for UI")
    except Exception as maya_check_error:
        # Maya commands not available or not running
        print(f"PyMEL available but Maya not running: {maya_check_error}")
        MAYA_AVAILABLE = False
        facial_pose_animator = None
except ImportError as e:
    print(f"Warning: Maya/PyMEL not available. Running in standalone mode. Error: {e}")
    MAYA_AVAILABLE = False
    facial_pose_animator = None
    # Define dummy exception classes for standalone mode
    class FacialAnimatorError(Exception): pass
    class ControlSelectionError(FacialAnimatorError): pass
    class DriverNodeError(FacialAnimatorError): pass
    class InvalidAttributeError(FacialAnimatorError): pass
    class FileOperationError(FacialAnimatorError): pass
    class ObjectSetError(FacialAnimatorError): pass
    class PoseDataError(FacialAnimatorError): pass


class PoseInfoDialog(QDialog):
    """Dialog for displaying detailed pose information."""
    
    def __init__(self, pose_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.pose_data = pose_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Pose Information")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Pose details
        info_group = QGroupBox("Pose Details")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(f"<b>Name:</b> {self.pose_data.get('name', 'N/A')}"))
        info_layout.addWidget(QLabel(f"<b>Attribute Name:</b> {self.pose_data.get('attribute_name', 'N/A')}"))
        info_layout.addWidget(QLabel(f"<b>Description:</b> {self.pose_data.get('description', 'N/A')}"))
        info_layout.addWidget(QLabel(f"<b>Timestamp:</b> {self.pose_data.get('timestamp', 'N/A')}"))
        info_layout.addWidget(QLabel(f"<b>Maya Version:</b> {self.pose_data.get('maya_version', 'N/A')}"))
        
        controls = self.pose_data.get('controls', {})
        info_layout.addWidget(QLabel(f"<b>Number of Controls:</b> {len(controls)}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Controls table
        controls_group = QGroupBox("Controls and Attributes")
        controls_layout = QVBoxLayout()
        
        self.controls_table = QTableWidget()
        self.controls_table.setColumnCount(3)
        self.controls_table.setHorizontalHeaderLabels(["Control", "Attribute", "Value"])
        self.controls_table.horizontalHeader().setStretchLastSection(True)
        
        row = 0
        for control_name, attributes in controls.items():
            for attr_name, value in attributes.items():
                self.controls_table.insertRow(row)
                self.controls_table.setItem(row, 0, QTableWidgetItem(control_name))
                self.controls_table.setItem(row, 1, QTableWidgetItem(attr_name))
                self.controls_table.setItem(row, 2, QTableWidgetItem(f"{value:.4f}"))
                row += 1
        
        controls_layout.addWidget(self.controls_table)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class FacialPoseCreatorUI(QMainWindow):
    """Main UI window for the Facial Pose Creator."""
    
    def __init__(self, parent=None):
        super().__init__()
        mayaMainWindow = QApplication.instance().activeWindow()
        try:
            import pymel.core as pm
            mayaMainWindow = pm.ui.Window('MayaWindow').asQtObject()
            pm.ui.deleteUI('FacialPoseCreatorUI')
        except:
            pass
        
        self.setParent(mayaMainWindow)
        self.setWindowFlags(Qt.Window)
        self.setObjectName("FacialPoseCreatorUI")
        self.resize(900, 700)
        self.setMinimumSize(900, 700)
        
        # Set window title with version
        window_title = "Facial Pose Creator"
        if MAYA_AVAILABLE and 'facial_pose_animator' in globals():
            try:
                window_title = f"Facial Pose Creator v{__version__}"
            except:
                pass
        self.setWindowTitle(window_title)
        
        self.animator = None
        
        self.init_animator()
        self.init_ui()
        
    def init_animator(self):
        """Initialize the facial pose animator."""
        if MAYA_AVAILABLE and facial_pose_animator:
            try:
                self.animator = facial_pose_animator.FacialPoseAnimator()
                print("Facial Pose Animator initialized successfully with Maya integration.")
            except Exception as e:
                self.animator = None
                error_msg = f"Error initializing animator: {e}"
                print(error_msg)
                import traceback
                traceback.print_exc()
        else:
            self.animator = None
            print("Running in standalone mode without Maya integration.")
    
    def init_ui(self):
        """Initialize the user interface."""
        # Update window title with version
        window_title = "Facial Pose Creator"
        if MAYA_AVAILABLE and 'facial_pose_animator' in globals():
            try:
                window_title = f"Facial Pose Creator v{__version__}"
            except:
                pass
        self.setWindowTitle(window_title)
        self.setMinimumSize(900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tab pages
        self.create_setup_tab()
        self.create_pose_management_tab()
        self.create_driver_tab()
        self.create_settings_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Show welcome message
        if not MAYA_AVAILABLE or not self.animator:
            self.log_message("WARNING: Maya not detected. Some features may be unavailable.")
        else:
            self.log_message("Facial Pose Animator initialized successfully with Maya integration.")
        
        # Load current settings from animator
        self.load_settings_from_animator()
        
        # Update driver status display
        if MAYA_AVAILABLE and self.animator:
            QTimer.singleShot(100, self.update_driver_status_display)  # Delayed call to ensure UI is ready
        
    def load_settings_from_animator(self):
        """Load current settings from the animator into the UI."""
        if not self.animator:
            self.log_message("Animator not available. Using default settings.")
            return
        
        try:
            # Load tolerance
            self.tolerance_spinbox.setValue(self.animator.tolerance)
            
            # Load undo tracking
            self.undo_tracking_check.setChecked(self.animator.enable_undo_tracking)
            
            # Load excluded nodes
            self.excluded_nodes_edit.setPlainText('\n'.join(self.animator.excluded_nodes))
            
            # Load excluded attributes
            self.excluded_attrs_edit.setPlainText('\n'.join(self.animator.excluded_attributes))
            
            # Load limit type map from animator
            self.limits_table.setRowCount(0)  # Clear existing rows
            
            # Check if the method exists (for backward compatibility with older animator versions)
            if hasattr(self.animator, 'get_limit_type_map_as_dict'):
                limit_mappings = self.animator.get_limit_type_map_as_dict()
                for attr_name, query_type in limit_mappings.items():
                    row = self.limits_table.rowCount()
                    self.limits_table.insertRow(row)
                    self.limits_table.setItem(row, 0, QTableWidgetItem(attr_name))
                    self.limits_table.setItem(row, 1, QTableWidgetItem(query_type))
            else:
                # Fallback: manually extract from limit_type_map if method doesn't exist
                self.log_message("Note: Using older animator version. Please reload the module for full functionality.")
                if hasattr(self.animator, 'limit_type_map'):
                    query_type_map = {
                        'translateX': 'tx', 'translateY': 'ty', 'translateZ': 'tz',
                        'rotateX': 'rx', 'rotateY': 'ry', 'rotateZ': 'rz',
                        'scaleX': 'sx', 'scaleY': 'sy', 'scaleZ': 'sz'
                    }
                    for attr_name in self.animator.limit_type_map.keys():
                        row = self.limits_table.rowCount()
                        self.limits_table.insertRow(row)
                        query_type = query_type_map.get(attr_name, 'tx')
                        self.limits_table.setItem(row, 0, QTableWidgetItem(attr_name))
                        self.limits_table.setItem(row, 1, QTableWidgetItem(query_type))
            
            # Load custom limit overrides
            self.custom_limits_table.setRowCount(0)  # Clear existing rows
            
            if hasattr(self.animator, 'get_all_custom_limits'):
                custom_limits = self.animator.get_all_custom_limits()
                for attr_name, (min_val, max_val) in custom_limits.items():
                    row = self.custom_limits_table.rowCount()
                    self.custom_limits_table.insertRow(row)
                    self.custom_limits_table.setItem(row, 0, QTableWidgetItem(attr_name))
                    self.custom_limits_table.setItem(row, 1, QTableWidgetItem(str(min_val)))
                    self.custom_limits_table.setItem(row, 2, QTableWidgetItem(str(max_val)))
            
            self.log_message("Loaded current settings from animator.")
            
        except Exception as e:
            self.log_message(f"Warning: Could not load all settings from animator: {e}")
    
    def create_setup_tab(self):
        """Create the setup tab for initial configuration."""
        setup_tab = QWidget()
        layout = QVBoxLayout()
        
        # Control Selection Group
        control_group = QGroupBox("Control Selection")
        control_layout = QVBoxLayout()
        
        # Selection mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Selection Mode:"))
        self.selection_mode_combo = QComboBox()
        self.selection_mode_combo.addItems(["Pattern", "Current Selection", "Object Set", "Metadata"])
        mode_layout.addWidget(self.selection_mode_combo)
        mode_layout.addStretch()
        control_layout.addLayout(mode_layout)
        
        # Control pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Control Pattern:"))
        self.control_pattern_edit = QLineEdit("::*_CTRL")
        pattern_layout.addWidget(self.control_pattern_edit)
        control_layout.addLayout(pattern_layout)
        
        # Object set
        set_layout = QHBoxLayout()
        set_layout.addWidget(QLabel("Object Set:"))
        self.object_set_edit = QLineEdit()
        set_layout.addWidget(self.object_set_edit)
        self.create_set_btn = QPushButton("Create Set")
        self.create_set_btn.clicked.connect(self.create_object_set)
        set_layout.addWidget(self.create_set_btn)
        control_layout.addLayout(set_layout)
        
        # Get controls button
        self.get_controls_btn = QPushButton("Get Facial Controls")
        self.get_controls_btn.clicked.connect(self.get_controls)
        control_layout.addWidget(self.get_controls_btn)
        
        # Controls list
        control_layout.addWidget(QLabel("Found Controls:"))
        self.controls_list = QListWidget()
        self.controls_list.setMaximumHeight(150)
        control_layout.addWidget(self.controls_list)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Driver Node Group
        driver_group = QGroupBox("Driver Node Setup")
        driver_layout = QVBoxLayout()
        
        # Current driver status display
        status_layout = QVBoxLayout()
        status_header = QLabel("<b>Current Driver Status:</b>")
        status_layout.addWidget(status_header)
        
        self.driver_status_label = QLabel("No driver node found")
        self.driver_status_label.setStyleSheet("color: gray; padding: 5px;")
        self.driver_status_label.setWordWrap(True)
        status_layout.addWidget(self.driver_status_label)
        
        # Refresh button for driver status
        refresh_layout = QHBoxLayout()
        self.refresh_driver_status_btn = QPushButton("Refresh Driver Status")
        self.refresh_driver_status_btn.clicked.connect(self.update_driver_status_display)
        self.refresh_driver_status_btn.setMaximumWidth(150)
        refresh_layout.addWidget(self.refresh_driver_status_btn)
        refresh_layout.addStretch()
        status_layout.addLayout(refresh_layout)
        
        driver_layout.addLayout(status_layout)
        
        # Separator
        separator = QLabel()
        separator.setFrameStyle(QLabel.HLine | QLabel.Sunken)
        driver_layout.addWidget(separator)
        
        # Driver node name
        driver_name_layout = QHBoxLayout()
        driver_name_layout.addWidget(QLabel("Driver Node Name:"))
        self.driver_name_edit = QLineEdit("FacialPoseValue")
        self.driver_name_edit.textChanged.connect(self.on_driver_name_changed)
        driver_name_layout.addWidget(self.driver_name_edit)
        driver_layout.addLayout(driver_name_layout)
        
        # Create driver button
        self.create_driver_btn = QPushButton("Create Facial Pose Driver")
        self.create_driver_btn.clicked.connect(self.create_driver)
        driver_layout.addWidget(self.create_driver_btn)
        
        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)
        
        # Auto-Animation Group
        animation_group = QGroupBox("Auto-Animate Poses")
        animation_layout = QVBoxLayout()
        
        animation_info_label = QLabel(
            "Automatically animate each control's attributes to their limits,\n"
            "save as poses, and auto-key each pose as a frame."
        )
        animation_info_label.setWordWrap(True)
        animation_layout.addWidget(animation_info_label)
        
        # Output file for pose names (optional)
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output File (optional):"))
        self.pose_names_output_edit = QLineEdit()
        self.pose_names_output_edit.setPlaceholderText("Leave empty or specify path for pose names list")
        output_layout.addWidget(self.pose_names_output_edit)
        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.browse_output_btn)
        animation_layout.addLayout(output_layout)
        
        # Animate button
        self.animate_poses_btn = QPushButton("Animate Facial Poses")
        self.animate_poses_btn.setToolTip(
            "Automatically animate all facial controls to their attribute limits,\n"
            "creating keyframes for each pose. Each pose gets its own frame."
        )
        self.animate_poses_btn.clicked.connect(self.animate_facial_poses_handler)
        animation_layout.addWidget(self.animate_poses_btn)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
        layout.addStretch()
        setup_tab.setLayout(layout)
        self.tabs.addTab(setup_tab, "Setup")
    
    def create_pose_management_tab(self):
        """Create the pose management tab."""
        pose_tab = QWidget()
        layout = QVBoxLayout()
        
        # Splitter for poses list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Poses list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("<b>Saved Poses</b>"))
        self.poses_list = QListWidget()
        self.poses_list.itemClicked.connect(self.on_pose_selected)
        left_layout.addWidget(self.poses_list)
        
        # Pose list buttons
        list_buttons_layout = QHBoxLayout()
        self.refresh_poses_btn = QPushButton("Refresh")
        self.refresh_poses_btn.clicked.connect(self.refresh_poses_list)
        list_buttons_layout.addWidget(self.refresh_poses_btn)
        
        self.delete_pose_btn = QPushButton("Delete")
        self.delete_pose_btn.clicked.connect(self.delete_pose)
        list_buttons_layout.addWidget(self.delete_pose_btn)
        
        left_layout.addLayout(list_buttons_layout)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right side - Pose creation/editing
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create pose group
        create_group = QGroupBox("Create/Save Pose")
        create_layout = QVBoxLayout()
        
        # Pose name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Pose Name:"))
        self.pose_name_edit = QLineEdit()
        name_layout.addWidget(self.pose_name_edit)
        create_layout.addLayout(name_layout)
        
        # Pose description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.pose_description_edit = QTextEdit()
        self.pose_description_edit.setMaximumHeight(60)
        desc_layout.addWidget(self.pose_description_edit)
        create_layout.addLayout(desc_layout)
        
        # Save options
        options_layout = QVBoxLayout()
        self.save_from_selection_check = QCheckBox("Save from current selection only")
        self.save_from_selection_check.setChecked(False)
        options_layout.addWidget(self.save_from_selection_check)
        
        self.include_zero_values_check = QCheckBox("Include zero/default values")
        self.include_zero_values_check.setChecked(False)
        self.include_zero_values_check.setToolTip(
            "If checked, saves all attribute values including zeros.\n"
            "Useful for saving neutral/rest poses."
        )
        options_layout.addWidget(self.include_zero_values_check)
        
        self.create_driver_attr_check = QCheckBox("Create driver attribute")
        self.create_driver_attr_check.setChecked(True)
        options_layout.addWidget(self.create_driver_attr_check)
        create_layout.addLayout(options_layout)
        
        # Save button
        self.save_pose_btn = QPushButton("Save Pose")
        self.save_pose_btn.clicked.connect(self.save_pose)
        create_layout.addWidget(self.save_pose_btn)
        
        create_group.setLayout(create_layout)
        right_layout.addWidget(create_group)
        
        # Load/Apply pose group
        apply_group = QGroupBox("Load/Apply Pose")
        apply_layout = QVBoxLayout()
        
        self.apply_pose_btn = QPushButton("Apply Selected Pose")
        self.apply_pose_btn.clicked.connect(self.apply_pose)
        apply_layout.addWidget(self.apply_pose_btn)
        
        self.view_pose_info_btn = QPushButton("View Pose Info")
        self.view_pose_info_btn.clicked.connect(self.view_pose_info)
        apply_layout.addWidget(self.view_pose_info_btn)
        
        apply_group.setLayout(apply_layout)
        right_layout.addWidget(apply_group)
        
        # File operations group
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        # File path
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(QLabel("File:"))
        self.poses_file_edit = QLineEdit()
        file_path_layout.addWidget(self.poses_file_edit)
        self.browse_file_btn = QPushButton("Browse")
        self.browse_file_btn.clicked.connect(self.browse_poses_file)
        file_path_layout.addWidget(self.browse_file_btn)
        file_layout.addLayout(file_path_layout)
        
        # File operation buttons
        file_buttons_layout = QHBoxLayout()
        self.load_poses_btn = QPushButton("Load from File")
        self.load_poses_btn.clicked.connect(self.load_poses_from_file)
        file_buttons_layout.addWidget(self.load_poses_btn)
        
        self.save_poses_btn = QPushButton("Save to File")
        self.save_poses_btn.clicked.connect(self.save_poses_to_file)
        file_buttons_layout.addWidget(self.save_poses_btn)
        
        file_layout.addLayout(file_buttons_layout)
        file_group.setLayout(file_layout)
        right_layout.addWidget(file_group)
        
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        pose_tab.setLayout(layout)
        self.tabs.addTab(pose_tab, "Pose Management")
    
    def create_driver_tab(self):
        """Create the driver management tab."""
        driver_tab = QWidget()
        layout = QVBoxLayout()
        
        # Driver info group
        info_group = QGroupBox("Driver Information")
        info_layout = QVBoxLayout()
        
        self.driver_info_text = QTextEdit()
        self.driver_info_text.setReadOnly(True)
        self.driver_info_text.setMaximumHeight(150)
        info_layout.addWidget(self.driver_info_text)
        
        self.get_driver_info_btn = QPushButton("Get Driver Info")
        self.get_driver_info_btn.clicked.connect(self.get_driver_info)
        info_layout.addWidget(self.get_driver_info_btn)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Register Control group
        register_group = QGroupBox("Register Control to Driver")
        register_layout = QVBoxLayout()
        
        register_info_label = QLabel(
            "Select a control in Maya, then click the button below to register it to the driver node.\n"
            "This will create pose attributes for all valid attributes of the selected control."
        )
        register_info_label.setWordWrap(True)
        register_layout.addWidget(register_info_label)
        
        self.register_selected_control_btn = QPushButton("Register Selected Control")
        self.register_selected_control_btn.setToolTip(
            "Register the currently selected control to the driver node.\n"
            "Creates pose attributes for all valid attributes."
        )
        self.register_selected_control_btn.clicked.connect(self.register_selected_control_to_driver)
        register_layout.addWidget(self.register_selected_control_btn)
        
        register_group.setLayout(register_layout)
        layout.addWidget(register_group)
        
        # Driver attributes group
        attrs_group = QGroupBox("Driver Attributes")
        attrs_layout = QVBoxLayout()
        
        self.driver_attrs_list = QListWidget()
        attrs_layout.addWidget(self.driver_attrs_list)
        
        attrs_buttons_layout = QHBoxLayout()
        self.refresh_attrs_btn = QPushButton("Refresh Attributes")
        self.refresh_attrs_btn.clicked.connect(self.refresh_driver_attributes)
        attrs_buttons_layout.addWidget(self.refresh_attrs_btn)
        
        self.test_attr_btn = QPushButton("Test Selected Attribute")
        self.test_attr_btn.clicked.connect(self.test_driver_attribute)
        attrs_buttons_layout.addWidget(self.test_attr_btn)
        
        attrs_layout.addLayout(attrs_buttons_layout)
        attrs_group.setLayout(attrs_layout)
        layout.addWidget(attrs_group)
        
        layout.addStretch()
        driver_tab.setLayout(layout)
        self.tabs.addTab(driver_tab, "Driver")
    
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_tab = QWidget()
        layout = QVBoxLayout()
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()
        
        # Tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_spinbox = QDoubleSpinBox()
        self.tolerance_spinbox.setRange(0.001, 1.0)
        self.tolerance_spinbox.setSingleStep(0.01)
        self.tolerance_spinbox.setValue(0.01)
        self.tolerance_spinbox.setDecimals(3)
        tolerance_layout.addWidget(self.tolerance_spinbox)
        tolerance_layout.addStretch()
        general_layout.addLayout(tolerance_layout)
        
        # Undo tracking
        self.undo_tracking_check = QCheckBox("Enable undo tracking")
        self.undo_tracking_check.setChecked(True)
        general_layout.addWidget(self.undo_tracking_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Excluded nodes group
        excluded_group = QGroupBox("Excluded Nodes")
        excluded_layout = QVBoxLayout()
        
        excluded_layout.addWidget(QLabel("Nodes containing these strings will be excluded:"))
        self.excluded_nodes_edit = QTextEdit()
        self.excluded_nodes_edit.setMaximumHeight(60)
        self.excluded_nodes_edit.setPlainText("GUI\npup")
        excluded_layout.addWidget(self.excluded_nodes_edit)
        
        excluded_group.setLayout(excluded_layout)
        layout.addWidget(excluded_group)
        
        # Excluded attributes group
        excluded_attrs_group = QGroupBox("Excluded Attributes")
        excluded_attrs_layout = QVBoxLayout()
        
        excluded_attrs_layout.addWidget(QLabel("These attributes will be excluded:"))
        self.excluded_attrs_edit = QTextEdit()
        self.excluded_attrs_edit.setMaximumHeight(60)
        self.excluded_attrs_edit.setPlainText("scaleX\nscaleY\nscaleZ")
        excluded_attrs_layout.addWidget(self.excluded_attrs_edit)
        
        excluded_attrs_group.setLayout(excluded_attrs_layout)
        layout.addWidget(excluded_attrs_group)
        
        # Transform limits group
        limits_group = QGroupBox("Transform Limit Queries")
        limits_layout = QVBoxLayout()
        
        limits_info_label = QLabel(
            "Configure which attributes use transform limits for value ranges:\n"
            "Query types: tx/ty/tz (translate), rx/ry/rz (rotate), sx/sy/sz (scale)"
        )
        limits_info_label.setWordWrap(True)
        limits_layout.addWidget(limits_info_label)
        
        # Table for limit type mappings
        self.limits_table = QTableWidget()
        self.limits_table.setColumnCount(2)
        self.limits_table.setHorizontalHeaderLabels(["Attribute", "Query Type"])
        self.limits_table.horizontalHeader().setStretchLastSection(True)
        self.limits_table.setMaximumHeight(120)
        self.limits_table.setToolTip(
            "Map Maya attribute names to their transform limit query types.\n"
            "Example: 'translateX' -> 'tx' will query translation limits on X axis."
        )
        
        # Populate with default values (will be overwritten by load_settings_from_animator if animator is available)
        default_limits = [
            ("translateX", "tx"),
            ("translateY", "ty"),
            ("translateZ", "tz")
        ]
        
        for attr, query_type in default_limits:
            row = self.limits_table.rowCount()
            self.limits_table.insertRow(row)
            self.limits_table.setItem(row, 0, QTableWidgetItem(attr))
            self.limits_table.setItem(row, 1, QTableWidgetItem(query_type))
        
        limits_layout.addWidget(self.limits_table)
        
        # Buttons for managing limits
        limits_buttons_layout = QHBoxLayout()
        self.add_limit_btn = QPushButton("Add Limit")
        self.add_limit_btn.clicked.connect(self.add_limit_mapping)
        limits_buttons_layout.addWidget(self.add_limit_btn)
        
        self.remove_limit_btn = QPushButton("Remove Selected")
        self.remove_limit_btn.clicked.connect(self.remove_limit_mapping)
        limits_buttons_layout.addWidget(self.remove_limit_btn)
        
        limits_buttons_layout.addStretch()
        limits_layout.addLayout(limits_buttons_layout)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        # Custom limit overrides group
        custom_limits_group = QGroupBox("Custom Limit Overrides")
        custom_limits_layout = QVBoxLayout()
        
        custom_limits_info_label = QLabel(
            "Define custom min/max limits for specific attributes.\n"
            "These override both transform limits and attribute ranges.\n"
            "Use exact attribute names (e.g., 'translateX', 'rotateY', 'customAttr')."
        )
        custom_limits_info_label.setWordWrap(True)
        custom_limits_layout.addWidget(custom_limits_info_label)
        
        # Table for custom limits
        self.custom_limits_table = QTableWidget()
        self.custom_limits_table.setColumnCount(3)
        self.custom_limits_table.setHorizontalHeaderLabels(["Attribute", "Min Value", "Max Value"])
        self.custom_limits_table.horizontalHeader().setStretchLastSection(True)
        self.custom_limits_table.setMaximumHeight(150)
        self.custom_limits_table.setToolTip(
            "Set custom limit ranges for attributes.\n"
            "Example: 'translateX' with min=-10.0, max=10.0"
        )
        custom_limits_layout.addWidget(self.custom_limits_table)
        
        # Buttons for managing custom limits
        custom_limits_buttons_layout = QHBoxLayout()
        self.add_custom_limit_btn = QPushButton("Add Custom Limit")
        self.add_custom_limit_btn.clicked.connect(self.add_custom_limit)
        custom_limits_buttons_layout.addWidget(self.add_custom_limit_btn)
        
        self.remove_custom_limit_btn = QPushButton("Remove Selected")
        self.remove_custom_limit_btn.clicked.connect(self.remove_custom_limit)
        custom_limits_buttons_layout.addWidget(self.remove_custom_limit_btn)
        
        self.clear_custom_limits_btn = QPushButton("Clear All")
        self.clear_custom_limits_btn.clicked.connect(self.clear_custom_limits)
        custom_limits_buttons_layout.addWidget(self.clear_custom_limits_btn)
        
        custom_limits_buttons_layout.addStretch()
        custom_limits_layout.addLayout(custom_limits_buttons_layout)
        
        custom_limits_group.setLayout(custom_limits_layout)
        layout.addWidget(custom_limits_group)
        
        # Apply settings button
        self.apply_settings_btn = QPushButton("Apply Settings")
        self.apply_settings_btn.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_settings_btn)
        
        layout.addStretch()
        settings_tab.setLayout(layout)
        self.tabs.addTab(settings_tab, "Settings")
    
    # Event handlers
    
    def log_message(self, message: str):
        """Add a message to the log."""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def get_controls(self):
        """Get facial controls based on current settings."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized. Maya may not be available.")
            return
        
        try:
            mode_text = self.selection_mode_combo.currentText()
            mode_map = {
                "Pattern": facial_pose_animator.ControlSelectionMode.PATTERN,
                "Current Selection": facial_pose_animator.ControlSelectionMode.SELECTION,
                "Object Set": facial_pose_animator.ControlSelectionMode.OBJECT_SET,
                "Metadata": facial_pose_animator.ControlSelectionMode.METADATA
            }
            
            mode = mode_map.get(mode_text, facial_pose_animator.ControlSelectionMode.PATTERN)
            
            # Update animator settings
            self.animator.control_pattern = self.control_pattern_edit.text()
            
            # Get controls
            controls = self.animator.get_facial_controls(
                mode=mode,
                object_set_name=self.object_set_edit.text() if self.object_set_edit.text() else None
            )
            
            # Update list
            self.controls_list.clear()
            for control in controls:
                self.controls_list.addItem(control.nodeName())
            
            self.log_message(f"Found {len(controls)} facial controls using {mode_text} mode.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get controls: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def create_object_set(self):
        """Create an object set from current selection."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        set_name = self.object_set_edit.text()
        if not set_name:
            QMessageBox.warning(self, "Warning", "Please enter a set name.")
            return
        
        try:
            result = self.animator.create_facial_control_set(set_name, use_current_selection=True)
            if result:
                self.log_message(f"Created object set: {set_name}")
                QMessageBox.information(self, "Success", f"Created object set: {set_name}")
            else:
                self.log_message(f"Failed to create object set: {set_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create set: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def create_driver(self):
        """Create the facial pose driver node with improved error handling."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        try:
            driver_name = self.driver_name_edit.text()
            if driver_name:
                # Set the driver node name on the animator instance
                self.animator.facial_driver_node = driver_name
            
            mode_text = self.selection_mode_combo.currentText()
            mode_map = {
                "Pattern": facial_pose_animator.ControlSelectionMode.PATTERN,
                "Current Selection": facial_pose_animator.ControlSelectionMode.SELECTION,
                "Object Set": facial_pose_animator.ControlSelectionMode.OBJECT_SET,
                "Metadata": facial_pose_animator.ControlSelectionMode.METADATA
            }
            mode = mode_map.get(mode_text, facial_pose_animator.ControlSelectionMode.PATTERN)
            
            # Get object set name if in OBJECT_SET mode
            object_set_name = None
            if mode == facial_pose_animator.ControlSelectionMode.OBJECT_SET:
                object_set_name = self.object_set_edit.text()
                if not object_set_name:
                    QMessageBox.warning(self, "Warning", "Object Set mode requires a set name.")
                    return
            
            # Use the new safe_create_driver function
            # Note: driver_node name is set on animator instance, not passed as parameter
            result = safe_create_driver(
                mode=mode,
                object_set_name=object_set_name
            )
            
            if result:
                self.log_message(f"Created facial pose driver: {result}")
                self.update_driver_status_display()  # Refresh driver status
                QMessageBox.information(self, "Success", f"Created driver node: {result}")
            else:
                self.log_message("Failed to create facial pose driver")
                QMessageBox.warning(self, "Warning", "Could not create driver node. Check selection and controls.")
                
        except ControlSelectionError as e:
            error_msg = f"Control selection error: {str(e)}"
            QMessageBox.warning(self, "Control Selection Error", error_msg)
            self.log_message(f"CONTROL SELECTION ERROR: {error_msg}")
            self.update_driver_status_display()
        except DriverNodeError as e:
            error_msg = f"Driver node error: {str(e)}"
            QMessageBox.warning(self, "Driver Node Error", error_msg)
            self.log_message(f"DRIVER NODE ERROR: {error_msg}")
            self.update_driver_status_display()
        except FacialAnimatorError as e:
            error_msg = f"Failed to create driver: {str(e)}"
            QMessageBox.critical(self, "Animator Error", error_msg)
            self.log_message(f"ANIMATOR ERROR: {error_msg}")
            self.update_driver_status_display()
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.log_message(f"ERROR: {error_msg}")
            self.update_driver_status_display()
    
    def browse_output_file(self):
        """Browse for output file to save pose names."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File for Pose Names", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.pose_names_output_edit.setText(file_path)
    
    def on_driver_name_changed(self, text):
        """Handle driver name text changes."""
        # Update animator's driver node name
        if self.animator:
            self.animator.facial_driver_node = text
        # Debounce the status update to avoid too many refreshes while typing
        if hasattr(self, '_driver_name_timer'):
            self._driver_name_timer.stop()
        self._driver_name_timer = QTimer()
        self._driver_name_timer.setSingleShot(True)
        self._driver_name_timer.timeout.connect(self.update_driver_status_display)
        self._driver_name_timer.start(500)  # Wait 500ms after last keystroke
    
    def update_driver_status_display(self):
        """Update the driver node status display in the UI."""
        if not self.animator:
            self.driver_status_label.setText("❌ Animator not initialized")
            self.driver_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffe6e6;")
            return
        
        try:
            driver_name = self.driver_name_edit.text()
            
            # Use animator's method to get driver pose attributes
            # This will handle driver node existence check internally
            try:
                pose_info_list = self.animator._get_driver_pose_attributes()
                num_poses = len(pose_info_list)
                
                # Import PyMEL only when we know driver exists to get the driver node
                import pymel.core as pm
                driver_nodes = pm.ls(driver_name)
                if driver_nodes:
                    driver_node = driver_nodes[0]
                    
                    # Get connected controls via metadata
                    connected_controls = self.animator._get_connected_facial_controls(driver_node)
                    num_controls = len(connected_controls)
                    
                    # Build status message
                    status_text = f"✅ Driver: <b>{driver_name}</b><br>"
                    status_text += f"📊 Poses: {num_poses}<br>"
                    status_text += f"🎭 Controls: {num_controls}"
                    
                    self.driver_status_label.setText(status_text)
                    self.driver_status_label.setStyleSheet(
                        "color: green; padding: 5px; background-color: #e6ffe6; border-left: 3px solid green;"
                    )
                    
                    self.log_message(f"Driver status updated: {driver_name} ({num_poses} poses, {num_controls} controls)")
                else:
                    # Shouldn't reach here, but handle just in case
                    raise Exception("Driver node lookup failed after successful pose query")
                    
            except Exception as e:
                # Check if this is a "not found" error from _get_driver_pose_attributes
                error_msg = str(e).lower()
                if "not found" in error_msg or "no driver node" in error_msg:
                    # Driver doesn't exist
                    status_text = f"❌ Driver: <b>{driver_name}</b><br>"
                    status_text += "Status: Not found in scene<br>"
                    status_text += "💡 Create driver using button below"
                    
                    self.driver_status_label.setText(status_text)
                    self.driver_status_label.setStyleSheet(
                        "color: gray; padding: 5px; background-color: #f5f5f5; border-left: 3px solid gray;"
                    )
                    self.log_message(f"Driver node '{driver_name}' not found in scene.")
                else:
                    # Driver exists but has issues
                    status_text = f"⚠️ Driver: <b>{driver_name}</b><br>"
                    status_text += "Status: Found but may have issues<br>"
                    status_text += f"Error: {str(e)[:50]}..."
                    
                    self.driver_status_label.setText(status_text)
                    self.driver_status_label.setStyleSheet(
                        "color: orange; padding: 5px; background-color: #fff4e6; border-left: 3px solid orange;"
                    )
                    self.log_message(f"Warning: Driver node exists but has issues: {e}")
                
        except ImportError:
            self.driver_status_label.setText("❌ PyMEL not available")
            self.driver_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffe6e6;")
            self.log_message("Cannot check driver status: PyMEL not available")
        except Exception as e:
            self.driver_status_label.setText(f"❌ Error checking status: {str(e)[:50]}")
            self.driver_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffe6e6;")
            self.log_message(f"Error updating driver status: {e}")
    
    def animate_facial_poses_handler(self):
        """Handler for auto-animating facial poses using the new unified API."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized. Maya may not be available.")
            return
        
        try:
            # Get selection mode
            mode_text = self.selection_mode_combo.currentText()
            mode_map = {
                "Pattern": facial_pose_animator.ControlSelectionMode.PATTERN,
                "Current Selection": facial_pose_animator.ControlSelectionMode.SELECTION,
                "Object Set": facial_pose_animator.ControlSelectionMode.OBJECT_SET,
                "Metadata": facial_pose_animator.ControlSelectionMode.METADATA
            }
            mode = mode_map.get(mode_text, facial_pose_animator.ControlSelectionMode.PATTERN)
            
            # Update animator settings
            self.animator.control_pattern = self.control_pattern_edit.text()
            
            # Get output file path (optional)
            output_file = self.pose_names_output_edit.text().strip()
            if not output_file:
                output_file = None
            
            # Get object set name if in OBJECT_SET mode
            object_set_name = None
            if mode == facial_pose_animator.ControlSelectionMode.OBJECT_SET:
                object_set_name = self.object_set_edit.text()
                if not object_set_name:
                    QMessageBox.warning(self, "Warning", "Object Set mode requires a set name.")
                    return
            
            # Show confirmation dialog
            try:
                controls = self.animator.get_facial_controls(
                    mode=mode,
                    object_set_name=object_set_name
                )
            except ControlSelectionError as e:
                QMessageBox.warning(self, "Control Selection Error", f"Cannot get controls: {str(e)}")
                self.log_message(f"CONTROL SELECTION ERROR: {str(e)}")
                return
            
            reply = QMessageBox.question(
                self,
                "Confirm Animation",
                f"This will animate {len(controls)} controls through their attribute limits,\n"
                f"creating keyframes for each pose. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                self.log_message("Animation cancelled by user.")
                return
            
            # Use the new safe_animate_poses function
            self.log_message("Starting facial pose animation...")
            self.log_message(f"Using selection mode: {mode_text}")
            self.statusBar().showMessage("Animating facial poses...")
            
            pose_names = safe_animate_poses(
                output_file=output_file,
                mode=mode,
                object_set_name=object_set_name
            )
            
            if pose_names:
                # Show success message
                self.log_message(f"Animation completed! Generated {len(pose_names)} poses.")
                if output_file:
                    self.log_message(f"Pose names written to: {output_file}")
                
                self.update_driver_status_display()  # Refresh driver status after animation
                self.statusBar().showMessage("Animation completed successfully.", 5000)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully animated {len(pose_names)} poses.\n"
                    f"Each pose has been keyed on a separate frame."
                )
            else:
                # safe_animate_poses returns None on error
                self.log_message("Animation failed or produced no poses.")
                self.statusBar().showMessage("Animation failed.", 5000)
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Animation completed but no poses were generated.\n"
                    "Check the log for details."
                )
            
        except ControlSelectionError as e:
            error_msg = f"Control selection error: {str(e)}"
            QMessageBox.warning(self, "Control Selection Error", error_msg)
            self.log_message(f"CONTROL SELECTION ERROR: {error_msg}")
            self.update_driver_status_display()
            self.statusBar().showMessage("Animation failed.", 5000)
        except DriverNodeError as e:
            error_msg = f"Driver node error: {str(e)}"
            QMessageBox.warning(self, "Driver Node Error", error_msg)
            self.log_message(f"DRIVER NODE ERROR: {error_msg}")
            self.update_driver_status_display()
            self.statusBar().showMessage("Animation failed.", 5000)
        except FacialAnimatorError as e:
            error_msg = f"Animation error: {str(e)}"
            QMessageBox.critical(self, "Animator Error", error_msg)
            self.log_message(f"ANIMATOR ERROR: {error_msg}")
            self.update_driver_status_display()
            self.statusBar().showMessage("Animation failed.", 5000)
        except Exception as e:
            error_msg = f"Unexpected error during animation: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.log_message(f"ERROR: {error_msg}")
            self.update_driver_status_display()
            self.statusBar().showMessage("Animation failed.", 5000)
    
    def save_pose(self):
        """Save a pose from current state with improved error handling."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        pose_name = self.pose_name_edit.text()
        if not pose_name:
            QMessageBox.warning(self, "Warning", "Please enter a pose name.")
            return
        
        try:
            description = self.pose_description_edit.toPlainText()
            from_selection = self.save_from_selection_check.isChecked()
            include_zeros = self.include_zero_values_check.isChecked()
            create_attr = self.create_driver_attr_check.isChecked()
            
            # Use the new safe_save_pose function for better error handling
            # Map checkbox state to ControlSelectionMode
            mode = ControlSelectionMode.SELECTION if from_selection else None
            pose_data = safe_save_pose(
                pose_name=pose_name,
                description=description,
                mode=mode,
                include_zero_values=include_zeros,
                save_to_file=True  # Auto-save to file in UI context
            )
            
            if not pose_data:
                self.log_message(f"Failed to save pose: {pose_name}")
                QMessageBox.warning(self, "Warning", f"Could not save pose '{pose_name}'. Check selection and controls.")
                return
            
            # Create driver attribute if requested
            if create_attr:
                try:
                    # Create driver attribute for the pose using animator method
                    # This adds the pose attribute to the existing driver node
                    success = self.animator.create_pose_driver_attribute(pose_name)
                    if success:
                        self.log_message(f"Created driver attribute for pose: {pose_name}")
                    else:
                        self.log_message(f"Note: Driver attribute may already exist for pose: {pose_name}")
                except Exception as attr_error:
                    self.log_message(f"Warning: Driver attribute creation failed: {attr_error}")
                    # Don't fail the whole operation if driver attribute creation fails
            
            self.log_message(f"Saved pose: {pose_name}")
            self.refresh_poses_list()
            QMessageBox.information(self, "Success", f"Saved pose: {pose_name}")
            
        except ControlSelectionError as e:
            QMessageBox.warning(self, "Selection Error", f"Invalid control selection: {str(e)}")
            self.log_message(f"SELECTION ERROR: {str(e)}")
        except PoseDataError as e:
            QMessageBox.warning(self, "Pose Data Error", f"Invalid pose data: {str(e)}")
            self.log_message(f"POSE DATA ERROR: {str(e)}")
        except FacialAnimatorError as e:
            QMessageBox.critical(self, "Animator Error", f"Failed to save pose: {str(e)}")
            self.log_message(f"ANIMATOR ERROR: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def refresh_poses_list(self):
        """Refresh the list of saved poses."""
        if not self.animator:
            return
        
        self.poses_list.clear()
        for pose_name in self.animator.saved_poses.keys():
            self.poses_list.addItem(pose_name)
        
        self.log_message(f"Refreshed poses list: {len(self.animator.saved_poses)} poses.")
    
    def on_pose_selected(self, item):
        """Handle pose selection in the list."""
        pose_name = item.text()
        self.log_message(f"Selected pose: {pose_name}")
    
    def delete_pose(self):
        """Delete the selected pose."""
        if not self.animator:
            return
        
        current_item = self.poses_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a pose to delete.")
            return
        
        pose_name = current_item.text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete pose '{pose_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self.animator.remove_saved_pose(pose_name)
                if result:
                    self.log_message(f"Deleted pose: {pose_name}")
                    self.refresh_poses_list()
                else:
                    self.log_message(f"Failed to delete pose: {pose_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete pose: {str(e)}")
                self.log_message(f"ERROR: {str(e)}")
    
    def apply_pose(self):
        """Apply the selected pose."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        current_item = self.poses_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a pose to apply.")
            return
        
        pose_name = current_item.text()
        try:
            result = self.animator.apply_saved_pose(pose_name)
            if result:
                self.log_message(f"Applied pose: {pose_name}")
                QMessageBox.information(self, "Success", f"Applied pose: {pose_name}")
            else:
                self.log_message(f"Failed to apply pose: {pose_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply pose: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def view_pose_info(self):
        """View detailed information about the selected pose."""
        if not self.animator:
            return
        
        current_item = self.poses_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a pose to view.")
            return
        
        pose_name = current_item.text()
        pose_data = self.animator.saved_poses.get(pose_name)
        
        if pose_data:
            dialog = PoseInfoDialog(pose_data.to_dict(), self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Error", f"Pose data not found for: {pose_name}")
    
    def browse_poses_file(self):
        """Browse for a poses file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Poses File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.poses_file_edit.setText(file_path)
    
    def load_poses_from_file(self):
        """Load poses from a file using the new unified API."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        file_path = self.poses_file_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file.")
            return
        
        try:
            # Use the new safe_load_poses function which handles errors gracefully
            result = safe_load_poses(
                file_path=file_path,
                overwrite_existing=True  # UI typically wants to overwrite
            )
            
            if result:
                self.log_message(f"Loaded {len(result)} poses from: {file_path}")
                self.refresh_poses_list()
                QMessageBox.information(self, "Success", f"Loaded {len(result)} poses from file.")
            else:
                # safe_load_poses returns None on error
                self.log_message(f"Failed to load poses from: {file_path}")
                QMessageBox.warning(self, "Warning", "No poses could be loaded from file.")
                
        except Exception as e:
            # Catch any unexpected errors
            QMessageBox.critical(self, "Error", f"Failed to load poses: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def save_poses_to_file(self):
        """Save poses to a file."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        file_path = self.poses_file_edit.text()
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Poses File", "", "JSON Files (*.json);;All Files (*)"
            )
            if file_path:
                self.poses_file_edit.setText(file_path)
        
        if not file_path:
            return
        
        try:
            self.animator.export_poses_to_file(file_path)
            self.log_message(f"Saved poses to: {file_path}")
            QMessageBox.information(self, "Success", f"Saved {len(self.animator.saved_poses)} poses to file.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save poses: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def get_driver_info(self):
        """Get information about the driver node."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        try:
            info = self.animator.get_driver_metadata_info()
            
            info_text = f"Driver Node: {info.get('driver_node', 'N/A')}\n"
            info_text += f"Exists: {info.get('exists', False)}\n"
            info_text += f"Connected Controls: {info.get('connected_controls_count', 0)}\n"
            info_text += f"Pose Attributes: {info.get('pose_attributes_count', 0)}\n\n"
            
            if info.get('connected_controls'):
                info_text += "Connected Controls:\n"
                for control in info['connected_controls']:
                    info_text += f"  - {control}\n"
            
            self.driver_info_text.setPlainText(info_text)
            self.log_message("Retrieved driver information.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get driver info: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def refresh_driver_attributes(self):
        """Refresh the list of driver attributes."""
        if not self.animator:
            return
        
        try:
            info = self.animator.get_driver_metadata_info()
            self.driver_attrs_list.clear()
            
            for attr in info.get('pose_attributes', []):
                self.driver_attrs_list.addItem(attr)
            
            self.log_message(f"Refreshed driver attributes: {len(info.get('pose_attributes', []))} attributes.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh attributes: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def register_selected_control_to_driver(self):
        """Register the currently selected control to the driver node."""
        if not MAYA_AVAILABLE or not self.animator:
            QMessageBox.warning(self, "Error", "Maya/Animator not available.")
            return
        
        try:
            self.log_message("Registering selected control to driver...")
            self.statusBar().showMessage("Registering control...")
            
            # Use the new safe function
            result = safe_register_selected_control_to_driver(
                driver_node_name=self.driver_name_edit.text(),
                update_metadata=True
            )
            
            if result and result.get('success'):
                control_name = result.get('control_name', 'Unknown')
                pose_count = result.get('pose_count', 0)
                
                success_msg = f"Successfully registered control: {control_name}\n"
                success_msg += f"Created {pose_count} pose attributes"
                
                QMessageBox.information(self, "Success", success_msg)
                self.log_message(f"Registered {control_name}: {pose_count} poses created")
                self.statusBar().showMessage("Control registered successfully", 3000)
                
                # Refresh the driver status display
                self.update_driver_status_display()
                
                # Refresh driver attributes list
                self.refresh_driver_attributes()
            else:
                errors = result.get('errors', ['Unknown error']) if result else ['No selection or operation failed']
                error_msg = "Failed to register control:\n" + "\n".join(errors)
                
                QMessageBox.warning(self, "Warning", error_msg)
                self.log_message(f"Failed to register control: {errors[0]}")
                self.statusBar().showMessage("Control registration failed", 3000)
                
        except Exception as e:
            error_msg = f"Error registering control: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.log_message(f"ERROR: {error_msg}")
            self.statusBar().showMessage("Error occurred", 3000)
    
    def test_driver_attribute(self):
        """Test the selected driver attribute."""
        current_item = self.driver_attrs_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an attribute to test.")
            return
        
        attr_name = current_item.text()
        self.log_message(f"Testing attribute: {attr_name}")
        QMessageBox.information(self, "Info", f"Testing feature for attribute '{attr_name}' is not yet implemented.")
    
    def add_limit_mapping(self):
        """Add a new limit mapping row."""
        row = self.limits_table.rowCount()
        self.limits_table.insertRow(row)
        self.limits_table.setItem(row, 0, QTableWidgetItem(""))
        self.limits_table.setItem(row, 1, QTableWidgetItem(""))
        self.log_message("Added new limit mapping row. Enter attribute name and query type (e.g., 'tx', 'ty', 'tz', 'rx', 'ry', 'rz').")
    
    def remove_limit_mapping(self):
        """Remove the selected limit mapping row."""
        current_row = self.limits_table.currentRow()
        if current_row >= 0:
            attr_name = self.limits_table.item(current_row, 0).text() if self.limits_table.item(current_row, 0) else ""
            self.limits_table.removeRow(current_row)
            self.log_message(f"Removed limit mapping for: {attr_name if attr_name else 'empty row'}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to remove.")
    
    def add_custom_limit(self):
        """Add a new custom limit row."""
        row = self.custom_limits_table.rowCount()
        self.custom_limits_table.insertRow(row)
        self.custom_limits_table.setItem(row, 0, QTableWidgetItem(""))
        self.custom_limits_table.setItem(row, 1, QTableWidgetItem("0.0"))
        self.custom_limits_table.setItem(row, 2, QTableWidgetItem("1.0"))
        self.log_message("Added new custom limit row. Enter attribute name, min value, and max value.")
    
    def remove_custom_limit(self):
        """Remove the selected custom limit row."""
        current_row = self.custom_limits_table.currentRow()
        if current_row >= 0:
            attr_name = self.custom_limits_table.item(current_row, 0).text() if self.custom_limits_table.item(current_row, 0) else ""
            self.custom_limits_table.removeRow(current_row)
            self.log_message(f"Removed custom limit for: {attr_name if attr_name else 'empty row'}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to remove.")
    
    def clear_custom_limits(self):
        """Clear all custom limit rows."""
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all custom limits?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.custom_limits_table.setRowCount(0)
            self.log_message("Cleared all custom limits from table.")
    
    def apply_settings(self):
        """Apply the current settings to the animator."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        try:
            # Update tolerance
            self.animator.tolerance = self.tolerance_spinbox.value()
            
            # Update undo tracking
            self.animator.set_undo_tracking(self.undo_tracking_check.isChecked())
            
            # Update excluded nodes
            excluded_nodes = [
                node.strip() for node in self.excluded_nodes_edit.toPlainText().split('\n')
                if node.strip()
            ]
            self.animator.excluded_nodes = excluded_nodes
            
            # Update excluded attributes
            excluded_attrs = [
                attr.strip() for attr in self.excluded_attrs_edit.toPlainText().split('\n')
                if attr.strip()
            ]
            self.animator.excluded_attributes = excluded_attrs
            
            # Update transform limit type map
            limit_mappings = {}
            
            for row in range(self.limits_table.rowCount()):
                attr_item = self.limits_table.item(row, 0)
                query_item = self.limits_table.item(row, 1)
                
                if attr_item and query_item:
                    attr_name = attr_item.text().strip()
                    query_type = query_item.text().strip()
                    
                    if attr_name and query_type:
                        limit_mappings[attr_name] = query_type
            
            # Use the animator's method to update the limit type map if available
            if hasattr(self.animator, 'update_limit_type_map'):
                results = self.animator.update_limit_type_map(limit_mappings)
                
                # Log results
                failed_mappings = [attr for attr, success in results.items() if not success]
                if failed_mappings:
                    self.log_message(f"WARNING: Invalid mappings for: {', '.join(failed_mappings)}")
                
                success_count = sum(1 for success in results.values() if success)
                self.log_message(f"Updated limit type map with {success_count} mappings.")
            else:
                # Fallback: directly update the limit_type_map (older version)
                self.log_message("Note: Using older animator version. Please reload the module for full functionality.")
                # We can't easily update lambdas without the helper method, so just log a warning
                self.log_message("WARNING: Limit type map updates require reloading the facial_pose_animator module.")
            
            # Update custom limit overrides (if available)
            if hasattr(self.animator, 'clear_custom_limits') and hasattr(self.animator, 'set_custom_limit'):
                self.animator.clear_custom_limits()
                custom_limits_count = 0
                custom_limits_errors = []
                
                for row in range(self.custom_limits_table.rowCount()):
                    attr_item = self.custom_limits_table.item(row, 0)
                    min_item = self.custom_limits_table.item(row, 1)
                    max_item = self.custom_limits_table.item(row, 2)
                    
                    if attr_item and min_item and max_item:
                        attr_name = attr_item.text().strip()
                        
                        if attr_name:
                            try:
                                min_value = float(min_item.text().strip())
                                max_value = float(max_item.text().strip())
                                
                                self.animator.set_custom_limit(attr_name, min_value, max_value)
                                custom_limits_count += 1
                            except ValueError as ve:
                                custom_limits_errors.append(f"{attr_name}: {str(ve)}")
                
                if custom_limits_count > 0:
                    self.log_message(f"Applied {custom_limits_count} custom limit override(s).")
                
                if custom_limits_errors:
                    error_msg = "Custom limit errors:\n" + "\n".join(custom_limits_errors)
                    self.log_message(f"WARNING: {error_msg}")
                    QMessageBox.warning(self, "Custom Limit Errors", error_msg)
            else:
                # Custom limits feature not available
                if self.custom_limits_table.rowCount() > 0:
                    self.log_message("WARNING: Custom limits feature requires reloading the facial_pose_animator module.")
            
            self.log_message("Settings applied successfully.")
            QMessageBox.information(self, "Success", "Settings applied successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")


def show_ui():
    """Show the Facial Pose Creator UI."""
    # Check if QApplication instance exists
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    
    # Create and show the main window
    window = FacialPoseCreatorUI(app)
    window.show()
    
    # Only start event loop if we created the QApplication (running standalone)
    # If QApplication already existed (e.g., running in Maya), don't start event loop
    if created_app:
        sys.exit(app.exec_())
    
    return window


if __name__ == "__main__":
    show_ui()
