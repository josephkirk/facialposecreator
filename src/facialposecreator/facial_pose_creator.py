"""
Facial Pose Creator UI
======================

A user interface for the Facial Pose Animation Tool for Maya.
Provides a comprehensive GUI for creating, managing, and animating facial control poses.

Author: Nguyen Phi Hung
Date: October 1, 2025
"""

import sys
import os
from typing import Optional, List, Dict, Any

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
    # Additional check: verify we're actually in Maya
    try:
        import maya.cmds as cmds
        # Check if Maya is actually running (not just imported)
        cmds.about(version=True)
        MAYA_AVAILABLE = True
        print("facial_pose_animator module imported successfully - Maya detected")
    except Exception as maya_check_error:
        # Maya commands not available or not running
        print(f"PyMEL available but Maya not running: {maya_check_error}")
        MAYA_AVAILABLE = False
        facial_pose_animator = None
except ImportError as e:
    print(f"Warning: Maya/PyMEL not available. Running in standalone mode. Error: {e}")
    MAYA_AVAILABLE = False
    facial_pose_animator = None


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
    
    def __init__(self):
        super().__init__()
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
        self.setWindowTitle("Facial Pose Creator")
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
        
        # Driver node name
        driver_name_layout = QHBoxLayout()
        driver_name_layout.addWidget(QLabel("Driver Node Name:"))
        self.driver_name_edit = QLineEdit("FacialPoseValue")
        driver_name_layout.addWidget(self.driver_name_edit)
        driver_layout.addLayout(driver_name_layout)
        
        # Create driver button
        self.create_driver_btn = QPushButton("Create Facial Pose Driver")
        self.create_driver_btn.clicked.connect(self.create_driver)
        driver_layout.addWidget(self.create_driver_btn)
        
        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)
        
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
                selection_mode=mode,
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
        """Create the facial pose driver node."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        try:
            driver_name = self.driver_name_edit.text()
            self.animator.facial_driver_node = driver_name
            
            mode_text = self.selection_mode_combo.currentText()
            mode_map = {
                "Pattern": facial_pose_animator.ControlSelectionMode.PATTERN,
                "Current Selection": facial_pose_animator.ControlSelectionMode.SELECTION,
                "Object Set": facial_pose_animator.ControlSelectionMode.OBJECT_SET,
                "Metadata": facial_pose_animator.ControlSelectionMode.METADATA
            }
            mode = mode_map.get(mode_text, facial_pose_animator.ControlSelectionMode.PATTERN)
            
            result = self.animator.create_facial_pose_driver(
                selection_mode=mode,
                object_set_name=self.object_set_edit.text() if self.object_set_edit.text() else None,
                create_metadata=True
            )
            
            if result:
                self.log_message(f"Created facial pose driver: {driver_name}")
                QMessageBox.information(self, "Success", f"Created driver node: {driver_name}")
            else:
                self.log_message("Failed to create driver node.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create driver: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def save_pose(self):
        """Save a pose from current state."""
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
            create_attr = self.create_driver_attr_check.isChecked()
            
            # Save the pose (always use save_pose_from_selection with use_current_selection parameter)
            pose_data = self.animator.save_pose_from_selection(
                pose_name=pose_name,
                description=description,
                use_current_selection=from_selection,
                create_driver_attribute=create_attr
            )
            
            if pose_data:
                self.log_message(f"Saved pose: {pose_name}")
                self.refresh_poses_list()
                QMessageBox.information(self, "Success", f"Saved pose: {pose_name}")
            else:
                self.log_message(f"Failed to save pose: {pose_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pose: {str(e)}")
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
        """Load poses from a file."""
        if not self.animator:
            QMessageBox.warning(self, "Error", "Animator not initialized.")
            return
        
        file_path = self.poses_file_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file.")
            return
        
        try:
            result = self.animator.import_poses_from_file(file_path)
            if result:
                self.log_message(f"Loaded poses from: {file_path}")
                self.refresh_poses_list()
                QMessageBox.information(self, "Success", f"Loaded {len(result)} poses from file.")
            else:
                self.log_message(f"Failed to load poses from: {file_path}")
        except Exception as e:
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
    
    def test_driver_attribute(self):
        """Test the selected driver attribute."""
        current_item = self.driver_attrs_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select an attribute to test.")
            return
        
        attr_name = current_item.text()
        self.log_message(f"Testing attribute: {attr_name}")
        QMessageBox.information(self, "Info", f"Testing feature for attribute '{attr_name}' is not yet implemented.")
    
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
