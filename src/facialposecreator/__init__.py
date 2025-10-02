"""
Facial Pose Creator Package
===========================

A comprehensive tool for automating facial pose creation in Autodesk Maya.

Main Components:
- facial_pose_animator: Core functionality for pose management and animation
- facial_pose_creator: GUI interface (PySide6/PySide2)

Author: Nguyen Phi Hung
Date: October 1, 2025
"""

# Version information
__version__ = '1.0.0'
__author__ = 'Nguyen Phi Hung'

# Import main components
try:
    from .facial_pose_animator import (
        FacialPoseAnimator,
        FacialPoseData,
        ControlSelectionMode,
        # Exceptions
        FacialAnimatorError,
        ControlSelectionError,
        InvalidAttributeError,
        DriverNodeError,
        FileOperationError,
        ObjectSetError,
        PoseDataError,
    )
    ANIMATOR_AVAILABLE = True
except ImportError as e:
    ANIMATOR_AVAILABLE = False
    print(f"Warning: facial_pose_animator not available: {e}")

# UI components (optional - may not be available without PySide)
try:
    from . import facial_pose_creator
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    facial_pose_creator = None

# Reload utilities (always available)
try:
    from . import reload_modules
    RELOAD_AVAILABLE = True
except ImportError:
    RELOAD_AVAILABLE = False
    reload_modules = None

# Convenience function to show UI
def show_ui():
    """
    Launch the Facial Pose Creator UI.
    
    Returns:
        The UI window object if successful, None otherwise.
    """
    if not UI_AVAILABLE:
        print("Error: UI not available. Please install PySide6 or PySide2.")
        return None
    
    return facial_pose_creator.show_ui()


# Convenience function to reload modules
def reload():
    """
    Reload all Facial Pose Creator modules.
    
    Useful during development to update modules without restarting Maya.
    
    Returns:
        Dictionary with reload statistics if successful, None otherwise.
    """
    if not RELOAD_AVAILABLE:
        print("Error: reload_modules not available.")
        return None
    
    return reload_modules.reload_all()


# Package info
def get_info():
    """Get package information."""
    info = {
        'version': __version__,
        'author': __author__,
        'animator_available': ANIMATOR_AVAILABLE,
        'ui_available': UI_AVAILABLE,
        'reload_available': RELOAD_AVAILABLE,
    }
    return info


# Public API
__all__ = [
    # Version info
    '__version__',
    '__author__',
    
    # Main classes (if available)
    'FacialPoseAnimator',
    'FacialPoseData',
    'ControlSelectionMode',
    
    # Exceptions
    'FacialAnimatorError',
    'ControlSelectionError',
    'InvalidAttributeError',
    'DriverNodeError',
    'FileOperationError',
    'ObjectSetError',
    'PoseDataError',
    
    # UI module
    'facial_pose_creator',
    
    # Reload utilities
    'reload_modules',
    
    # Functions
    'show_ui',
    'reload',
    'get_info',
    
    # Availability flags
    'ANIMATOR_AVAILABLE',
    'UI_AVAILABLE',
    'RELOAD_AVAILABLE',
]
