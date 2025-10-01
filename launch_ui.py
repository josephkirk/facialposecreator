"""
Launcher script for Facial Pose Creator UI
==========================================

Run this script to launch the Facial Pose Creator interface.
Works both standalone and within Maya.
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Try to import and launch the UI
try:
    from facialposecreator import facial_pose_creator
    
    # Show the UI
    window = facial_pose_creator.show_ui()
    print("Facial Pose Creator UI launched successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("\nPlease ensure PySide6 or PySide2 is installed:")
    print("  pip install PySide6")
    print("  or")
    print("  pip install PySide2")
    sys.exit(1)
except Exception as e:
    print(f"Error launching UI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
