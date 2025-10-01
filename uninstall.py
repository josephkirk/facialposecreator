"""
Facial Pose Tools - Maya Uninstaller
====================================

Drag and drop this file into Maya's viewport to uninstall the Facial Pose Tools.

This will remove:
1. The facialposecreator module from Maya's scripts directory
2. The shelf button
3. Module files and configuration

Author: Nguyen Phi Hung
Date: October 1, 2025
"""

import os
import sys
import shutil
from pathlib import Path

try:
    import maya.cmds as cmds
    import maya.mel as mel
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print("Warning: This uninstaller must be run from within Maya")


class FacialPoseToolsUninstaller:
    """Uninstaller for Facial Pose Tools in Maya."""
    
    def __init__(self):
        self.package_name = "facialposecreator"
        
        # Get Maya directories
        if MAYA_AVAILABLE:
            self.maya_app_dir = Path(cmds.internalVar(userAppDir=True))
            self.maya_scripts_dir = self.maya_app_dir / "scripts"
            self.maya_shelves_dir = self.maya_app_dir / "prefs" / "shelves"
            self.maya_modules_dir = self.maya_app_dir / "modules"
        else:
            self.maya_app_dir = None
            self.maya_scripts_dir = None
            self.maya_shelves_dir = None
            self.maya_modules_dir = None
        
        self.removed_items = []
    
    def remove_package(self):
        """Remove the facialposecreator package from Maya scripts directory."""
        package_dir = self.maya_scripts_dir / self.package_name
        
        if package_dir.exists():
            print(f"Removing package: {package_dir}")
            shutil.rmtree(package_dir)
            self.removed_items.append(f"Package directory: {package_dir}")
            print("✓ Package removed")
            return True
        else:
            print("Package directory not found (already removed or not installed)")
            return False
    
    def remove_shelf_button(self):
        """Remove the shelf button for Facial Pose Tools."""
        shelf_name = "Custom"
        button_label = "FacialPose"
        
        if not cmds.shelfLayout(shelf_name, exists=True):
            print(f"Shelf '{shelf_name}' not found")
            return False
        
        # Get all buttons on the shelf
        shelf_buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
        removed = False
        
        for button in shelf_buttons:
            try:
                label = cmds.shelfButton(button, query=True, label=True)
                if label == button_label:
                    print(f"Removing shelf button: {button}")
                    cmds.deleteUI(button)
                    self.removed_items.append(f"Shelf button: {button_label}")
                    removed = True
                    print("✓ Shelf button removed")
            except:
                pass
        
        if removed:
            # Save shelf
            try:
                mel.eval(f'saveAllShelves $gShelfTopLevel;')
                print("✓ Shelf saved")
            except:
                print("Note: Please save shelf manually if needed")
        else:
            print("Shelf button not found (already removed or not installed)")
        
        return removed
    
    def clean_usersetup(self):
        """Remove Facial Pose Tools entries from userSetup.py."""
        usersetup_path = self.maya_scripts_dir / "userSetup.py"
        
        if not usersetup_path.exists():
            print("userSetup.py not found")
            return False
        
        with open(usersetup_path, 'r') as f:
            lines = f.readlines()
        
        # Filter out lines related to Facial Pose Tools
        new_lines = []
        skip_block = False
        removed_lines = 0
        
        for line in lines:
            if "Facial Pose Tools" in line:
                skip_block = True
                removed_lines += 1
                continue
            
            if skip_block:
                # Skip empty lines and related code after marker
                if line.strip() == "" or line.startswith("import") or line.startswith("scripts_dir"):
                    removed_lines += 1
                    continue
                else:
                    skip_block = False
            
            new_lines.append(line)
        
        if removed_lines > 0:
            # Write back the cleaned content
            with open(usersetup_path, 'w') as f:
                f.writelines(new_lines)
            
            self.removed_items.append(f"userSetup.py entries ({removed_lines} lines)")
            print(f"✓ Cleaned userSetup.py ({removed_lines} lines removed)")
            return True
        else:
            print("No Facial Pose Tools entries found in userSetup.py")
            return False
    
    def remove_module_file(self):
        """Remove the .mod file."""
        mod_file = self.maya_modules_dir / f"{self.package_name}.mod"
        
        if mod_file.exists():
            print(f"Removing module file: {mod_file}")
            os.remove(mod_file)
            self.removed_items.append(f"Module file: {mod_file.name}")
            print("✓ Module file removed")
            return True
        else:
            print("Module file not found (already removed or not installed)")
            return False
    
    def uninstall(self):
        """Run the full uninstallation process."""
        print("="*60)
        print("Facial Pose Tools - Uninstallation")
        print("="*60)
        
        if not MAYA_AVAILABLE:
            print("ERROR: This uninstaller must be run from within Maya")
            print("Please drag and drop this file into Maya's viewport")
            return False
        
        # Confirm uninstallation
        result = cmds.confirmDialog(
            title="Uninstall Facial Pose Tools",
            message="Are you sure you want to uninstall Facial Pose Tools?\n\n"
                    "This will remove:\n"
                    "• The facialposecreator package\n"
                    "• Shelf button\n"
                    "• Module files\n"
                    "• Configuration entries\n",
            button=["Uninstall", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
            dismissString="Cancel"
        )
        
        if result != "Uninstall":
            print("Uninstallation cancelled by user")
            return False
        
        try:
            # Step 1: Remove package
            print("\n[1/4] Removing package...")
            self.remove_package()
            
            # Step 2: Remove shelf button
            print("\n[2/4] Removing shelf button...")
            self.remove_shelf_button()
            
            # Step 3: Clean userSetup.py
            print("\n[3/4] Cleaning userSetup.py...")
            self.clean_usersetup()
            
            # Step 4: Remove module file
            print("\n[4/4] Removing module file...")
            self.remove_module_file()
            
            print("\n" + "="*60)
            print("✓ Uninstallation Complete!")
            print("="*60)
            
            if self.removed_items:
                print("\nRemoved items:")
                for item in self.removed_items:
                    print(f"  • {item}")
            else:
                print("\nNo items were found to remove.")
                print("The Facial Pose Tools may not have been installed.")
            
            print("\nNote: You may need to restart Maya for all changes to take effect.")
            
            # Show confirmation dialog
            cmds.confirmDialog(
                title="Uninstallation Complete",
                message="Facial Pose Tools have been uninstalled successfully!\n\n"
                        "You may need to restart Maya for all changes to take effect.",
                button=["OK"],
                defaultButton="OK"
            )
            
            return True
            
        except Exception as e:
            print(f"\n✗ Uninstallation failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            cmds.confirmDialog(
                title="Uninstallation Failed",
                message=f"Uninstallation failed with error:\n\n{str(e)}\n\n"
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
    uninstaller = FacialPoseToolsUninstaller()
    uninstaller.uninstall()


# Allow running directly (for testing)
if __name__ == "__main__":
    if MAYA_AVAILABLE:
        uninstaller = FacialPoseToolsUninstaller()
        uninstaller.uninstall()
    else:
        print("This script must be run from within Maya")
        print("Drag and drop this file into Maya's viewport to uninstall")
