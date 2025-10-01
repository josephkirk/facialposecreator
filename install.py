"""
Facial Pose Tools - Maya Drag & Drop Installer
==============================================

Drag and drop this file into Maya's viewport to install the Facial Pose Tools.

This installer will:
1. Copy the facialposecreator module to Maya's scripts directory
2. Create a shelf button to launch the UI
3. Set up all necessary paths

Author: Nguyen Phi Hung
Date: October 1, 2025
"""

import os
import sys
import shutil
import json
from pathlib import Path

try:
    import maya.cmds as cmds
    import maya.mel as mel
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print("Warning: This installer must be run from within Maya")


class FacialPoseToolsInstaller:
    """Installer for Facial Pose Tools in Maya."""
    
    def __init__(self):
        self.install_dir = Path(__file__).parent
        self.src_dir = self.install_dir / "src"
        self.package_name = "facialposecreator"
        
        # Get Maya scripts directory
        if MAYA_AVAILABLE:
            self.maya_app_dir = Path(cmds.internalVar(userAppDir=True))
            self.maya_scripts_dir = self.maya_app_dir / "scripts"
            self.maya_shelves_dir = self.maya_app_dir / "prefs" / "shelves"
        else:
            self.maya_app_dir = None
            self.maya_scripts_dir = None
            self.maya_shelves_dir = None
    
    def validate_source(self):
        """Validate that source files exist."""
        if not self.src_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.src_dir}")
        
        package_dir = self.src_dir / self.package_name
        if not package_dir.exists():
            raise FileNotFoundError(f"Package directory not found: {package_dir}")
        
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
            raise FileNotFoundError(f"Package __init__.py not found: {init_file}")
        
        return True
    
    def copy_package(self):
        """Copy the facialposecreator package to Maya scripts directory."""
        source_package = self.src_dir / self.package_name
        dest_package = self.maya_scripts_dir / self.package_name
        
        # Remove existing installation if present
        if dest_package.exists():
            print(f"Removing existing installation: {dest_package}")
            shutil.rmtree(dest_package)
        
        # Copy package
        print(f"Copying {source_package} to {dest_package}")
        shutil.copytree(source_package, dest_package)
        
        # Verify installation
        if not dest_package.exists():
            raise Exception("Package copy failed")
        
        print(f"✓ Package installed to: {dest_package}")
        return dest_package
    
    def create_shelf_button(self):
        """Create a shelf button for the Facial Pose Tools."""
        shelf_name = "Custom"
        
        # Check if Custom shelf exists, create if not
        if not cmds.shelfLayout(shelf_name, exists=True):
            print(f"Creating shelf: {shelf_name}")
            mel.eval(f'addNewShelfTab("{shelf_name}")')
        
        # Make the shelf active
        mel.eval(f'global string $gShelfTopLevel; setParent $gShelfTopLevel;')
        
        # Python command to launch the UI
        python_command = '''
import sys
import maya.cmds as cmds

# Ensure the scripts directory is in path
scripts_dir = cmds.internalVar(userAppDir=True) + "scripts"
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# Import and show UI
try:
    import facialposecreator
    # Reload in case of updates
    import importlib
    importlib.reload(facialposecreator)
    if hasattr(facialposecreator, 'facial_pose_creator'):
        importlib.reload(facialposecreator.facial_pose_creator)
    
    facialposecreator.show_ui()
except Exception as e:
    cmds.warning(f"Error launching Facial Pose Tools: {e}")
    import traceback
    traceback.print_exc()
'''
        
        # Icon path (using Maya's default icon)
        icon_path = "face.png"  # Maya built-in icon
        
        # Check if button already exists
        shelf_buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
        button_label = "FacialPose"
        
        # Remove existing button if found
        for button in shelf_buttons:
            if cmds.shelfButton(button, query=True, label=True) == button_label:
                print(f"Removing existing button: {button}")
                cmds.deleteUI(button)
        
        # Create new shelf button
        cmds.shelfButton(
            parent=shelf_name,
            command=python_command,
            annotation="Launch Facial Pose Creator",
            label=button_label,
            image=icon_path,
            imageOverlayLabel="Face",
            sourceType="python"
        )
        
        print(f"✓ Shelf button created on '{shelf_name}' shelf")
        
        # Save shelf
        try:
            mel.eval(f'saveAllShelves $gShelfTopLevel;')
            print("✓ Shelf saved")
        except:
            print("Note: Please save shelf manually if needed")
    
    def create_userSetup(self):
        """Create or update userSetup.py to ensure the module is in path."""
        usersetup_path = self.maya_scripts_dir / "userSetup.py"
        
        setup_code = """
# Facial Pose Tools - Auto-generated setup
import sys
import maya.cmds as cmds

scripts_dir = cmds.internalVar(userAppDir=True) + "scripts"
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

print("Facial Pose Tools: Scripts directory added to path")
"""
        
        # Check if userSetup.py exists
        if usersetup_path.exists():
            with open(usersetup_path, 'r') as f:
                existing_content = f.read()
            
            # Check if our setup code is already there
            if "Facial Pose Tools" in existing_content:
                print("✓ userSetup.py already configured")
                return
            
            # Append to existing file
            with open(usersetup_path, 'a') as f:
                f.write("\n\n")
                f.write(setup_code)
            print("✓ Updated existing userSetup.py")
        else:
            # Create new file
            with open(usersetup_path, 'w') as f:
                f.write(setup_code)
            print("✓ Created userSetup.py")
    
    def create_module_file(self):
        """Create a .mod file for Maya module system (alternative approach)."""
        modules_dir = self.maya_app_dir / "modules"
        modules_dir.mkdir(exist_ok=True)
        
        mod_file = modules_dir / "facialposecreator.mod"
        
        # Module file content
        # Points to the installed package location
        scripts_dir = self.maya_scripts_dir.as_posix()
        
        mod_content = f"""+ facialposecreator 1.0 {scripts_dir}
PYTHONPATH+:={scripts_dir}
"""
        
        with open(mod_file, 'w') as f:
            f.write(mod_content)
        
        print(f"✓ Module file created: {mod_file}")
    
    def install(self):
        """Run the full installation process."""
        print("="*60)
        print("Facial Pose Tools - Installation")
        print("="*60)
        
        if not MAYA_AVAILABLE:
            print("ERROR: This installer must be run from within Maya")
            print("Please drag and drop this file into Maya's viewport")
            return False
        
        try:
            # Step 1: Validate source
            print("\n[1/5] Validating source files...")
            self.validate_source()
            print("✓ Source files validated")
            
            # Step 2: Copy package
            print("\n[2/5] Installing package...")
            self.copy_package()
            
            # Step 3: Create shelf button
            print("\n[3/5] Creating shelf button...")
            self.create_shelf_button()
            
            # Step 4: Update userSetup.py
            print("\n[4/5] Configuring Maya startup...")
            self.create_userSetup()
            
            # Step 5: Create module file
            print("\n[5/5] Creating module file...")
            self.create_module_file()
            
            print("\n" + "="*60)
            print("✓ Installation Complete!")
            print("="*60)
            print("\nThe Facial Pose Tools have been installed successfully.")
            print(f"\nInstallation location: {self.maya_scripts_dir / self.package_name}")
            print("\nYou can now:")
            print("  1. Click the 'Face' button on the Custom shelf")
            print("  2. Run: import facialposecreator; facialposecreator.show_ui()")
            print("\nNote: You may need to restart Maya for all changes to take effect.")
            
            # Show confirmation dialog
            result = cmds.confirmDialog(
                title="Installation Complete",
                message="Facial Pose Tools installed successfully!\n\n"
                        "Click the 'Face' button on the Custom shelf to launch.\n\n"
                        "Would you like to launch it now?",
                button=["Launch Now", "Close"],
                defaultButton="Launch Now",
                cancelButton="Close",
                dismissString="Close"
            )
            
            if result == "Launch Now":
                print("\nLaunching Facial Pose Tools...")
                try:
                    import facialposecreator
                    facialposecreator.show_ui()
                except Exception as e:
                    cmds.warning(f"Error launching UI: {e}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Installation failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            if MAYA_AVAILABLE:
                cmds.confirmDialog(
                    title="Installation Failed",
                    message=f"Installation failed with error:\n\n{str(e)}\n\n"
                            "Please check the Script Editor for details.",
                    button=["OK"],
                    defaultButton="OK"
                )
            
            return False


def onMayaDroppedPythonFile(*args, **kwargs):
    """
    This function is automatically called by Maya when a Python file
    is dragged and dropped into the viewport.
    """
    installer = FacialPoseToolsInstaller()
    installer.install()


# Allow running directly (for testing)
if __name__ == "__main__":
    if MAYA_AVAILABLE:
        installer = FacialPoseToolsInstaller()
        installer.install()
    else:
        print("This script must be run from within Maya")
        print("Drag and drop this file into Maya's viewport to install")
