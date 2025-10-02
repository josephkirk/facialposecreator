"""
Reload Facial Pose Creator Modules
====================================

Helper script to reload the facial_pose_animator and facial_pose_creator modules in Maya.
Run this after making changes to the Python files to update the running Maya session.

Usage in Maya Script Editor:
    from src.facialposecreator import reload_modules
    reload_modules.reload_all()
    
    # Or directly:
    from src.facialposecreator.reload_modules import reload_all
    reload_all()
"""

import sys
import importlib


def reload_all():
    """Reload all Facial Pose Creator modules."""
    
    # Order matters: reload base modules before UI
    modules_to_reload = [
        'src.facialposecreator.facial_pose_animator',
        'src.facialposecreator.facial_pose_creator',
        'src.facialposecreator'
    ]
    
    print("=" * 60)
    print("Reloading Facial Pose Creator Modules")
    print("=" * 60)
    
    reloaded_count = 0
    not_loaded_count = 0
    failed_count = 0
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                print(f"✓ Reloaded: {module_name}")
                reloaded_count += 1
            except Exception as e:
                print(f"✗ Failed to reload {module_name}: {e}")
                failed_count += 1
                import traceback
                traceback.print_exc()
        else:
            print(f"○ Module not loaded yet: {module_name}")
            not_loaded_count += 1
    
    print("=" * 60)
    print(f"Reload complete! (✓ {reloaded_count} | ○ {not_loaded_count} | ✗ {failed_count})")
    print("=" * 60)
    
    if reloaded_count > 0:
        print("\n✓ Modules successfully reloaded!")
        print("\nTo show the UI, run:")
        print("    from src.facialposecreator import facial_pose_creator")
        print("    facial_pose_creator.show_ui()")
    elif not_loaded_count > 0:
        print("\n○ No modules were loaded yet. Import them first:")
        print("    from src.facialposecreator import facial_pose_creator")
        print("    facial_pose_creator.show_ui()")
    
    if failed_count > 0:
        print("\n⚠ Some modules failed to reload. Check the error messages above.")
    
    return {
        'reloaded': reloaded_count,
        'not_loaded': not_loaded_count,
        'failed': failed_count
    }


def reload_animator_only():
    """Reload only the facial_pose_animator module."""
    print("Reloading facial_pose_animator module...")
    
    module_name = 'src.facialposecreator.facial_pose_animator'
    if module_name in sys.modules:
        try:
            importlib.reload(sys.modules[module_name])
            print(f"✓ Reloaded: {module_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to reload {module_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"○ Module not loaded yet: {module_name}")
        return False


def reload_ui_only():
    """Reload only the facial_pose_creator UI module."""
    print("Reloading facial_pose_creator UI module...")
    
    module_name = 'src.facialposecreator.facial_pose_creator'
    if module_name in sys.modules:
        try:
            importlib.reload(sys.modules[module_name])
            print(f"✓ Reloaded: {module_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to reload {module_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"○ Module not loaded yet: {module_name}")
        return False


if __name__ == "__main__":
    reload_all()
