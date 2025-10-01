#!/usr/bin/env python
"""
MayaPy Test Runner Script
========================

This script runs the facial_pose_animator unit tests within Maya's Python environment (mayapy.exe).
It provides a way to execute unit tests in the context where PyMEL and Maya are actually available.

Usage:
    # Run with mayapy.exe (Maya's standalone Python interpreter)
    mayapy.exe run_tests_with_mayapy.py
    
    # Run specific test class
    mayapy.exe run_tests_with_mayapy.py TestFacialPoseData
    
    # Run in verbose mode
    mayapy.exe run_tests_with_mayapy.py --verbose
    
    # Run without Maya initialization (for mock testing)
    mayapy.exe run_tests_with_mayapy.py --no-maya

Author: Test Suite
Date: Created for testing facial_pose_animator.py
"""

import sys
import os
import argparse
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def setup_maya_environment():
    """
    Initialize Maya environment for testing.
    
    Returns:
        bool: True if Maya initialized successfully, False otherwise
    """
    try:
        import maya.standalone
        maya.standalone.initialize(name='python')
        
        # Import Maya commands and PyMEL
        import maya.cmds as cmds
        import pymel.core as pm
        
        logger.info("Maya standalone environment initialized successfully")
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import Maya modules: {e}")
        logger.error("Make sure you're running this script with mayapy.exe")
        return False
        
    except Exception as e:
        logger.error(f"Failed to initialize Maya standalone: {e}")
        return False


def setup_test_environment():
    """
    Set up the testing environment with proper paths and imports.
    
    Returns:
        bool: True if setup successful, False otherwise
    """
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        logger.info(f"Added {current_dir} to Python path")
        
        # Verify that our test module can be imported
        try:
            import test_facial_pose_animator
            logger.info("Test module imported successfully")
            return True
        except ImportError as e:
            logger.error(f"Failed to import test module: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")
        return False


def run_tests_with_maya(test_class: Optional[str] = None, verbose: bool = False):
    """
    Run unit tests within Maya environment.
    
    Args:
        test_class: Specific test class to run (optional)
        verbose: Enable verbose output
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Import test modules
        from test_facial_pose_animator import FacialPoseAnimatorTestSuite
        import unittest
        
        logger.info("Running tests with Maya environment")
        
        # Create test runner with appropriate verbosity
        verbosity = 2 if verbose else 1
        
        if test_class:
            logger.info(f"Running specific test class: {test_class}")
            # Run specific test class
            suite = FacialPoseAnimatorTestSuite()
            result = suite.run_specific_test(test_class)
        else:
            logger.info("Running all test classes")
            # Run all tests
            suite = FacialPoseAnimatorTestSuite()
            result = suite.run_all_tests()
        
        # Print detailed results
        print("\n" + "=" * 60)
        print("MAYA ENVIRONMENT TEST RESULTS")
        print("=" * 60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success: {result.wasSuccessful()}")
        
        if result.failures:
            print("\nFAILURES:")
            for i, (test, traceback) in enumerate(result.failures, 1):
                print(f"\n{i}. {test}")
                print("-" * 40)
                print(traceback)
                
        if result.errors:
            print("\nERRORS:")
            for i, (test, traceback) in enumerate(result.errors, 1):
                print(f"\n{i}. {test}")
                print("-" * 40)
                print(traceback)
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_tests_without_maya(test_class: Optional[str] = None, verbose: bool = False):
    """
    Run unit tests without Maya initialization (uses mocks).
    
    Args:
        test_class: Specific test class to run (optional)
        verbose: Enable verbose output
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Import test modules (these should use mocks)
        from test_facial_pose_animator import FacialPoseAnimatorTestSuite
        import unittest
        
        logger.info("Running tests without Maya environment (using mocks)")
        
        if test_class:
            logger.info(f"Running specific test class: {test_class}")
            suite = FacialPoseAnimatorTestSuite()
            result = suite.run_specific_test(test_class)
        else:
            logger.info("Running all test classes")
            suite = FacialPoseAnimatorTestSuite()
            result = suite.run_all_tests()
        
        # Print results
        print("\n" + "=" * 60)
        print("MOCK ENVIRONMENT TEST RESULTS")
        print("=" * 60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success: {result.wasSuccessful()}")
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        logger.error(f"Error running mock tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


def create_maya_test_scene():
    """
    Create a minimal test scene with some facial controls for testing.
    
    Returns:
        List[str]: Names of created test controls
    """
    try:
        import maya.cmds as cmds
        
        # Clear scene
        cmds.file(new=True, force=True)
        
        # Create test facial controls
        test_controls = []
        
        # Create main facial controls
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
        
        logger.info(f"Created test scene with controls: {test_controls}")
        return test_controls
        
    except Exception as e:
        logger.error(f"Error creating test scene: {e}")
        return []


def run_integration_tests():
    """
    Run integration tests that actually use Maya functionality.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Running integration tests with real Maya functionality")
        
        # Create test scene
        test_controls = create_maya_test_scene()
        if not test_controls:
            logger.error("Failed to create test scene")
            return 1
            
        # Import the actual module (not mocked)
        from facial_pose_animator import FacialPoseAnimator, ControlSelectionMode
        
        # Create animator instance
        animator = FacialPoseAnimator()
        
        # Test basic functionality
        try:
            # Test scene validation
            validation = animator.validate_scene_setup()
            logger.info(f"Scene validation: {validation}")
            
            # Test control selection using pattern matching
            animator.control_pattern = "*_CTRL"  # Update pattern for our test controls
            controls = animator.get_facial_controls(mode=ControlSelectionMode.PATTERN)
            logger.info(f"Found {len(controls)} controls using pattern matching")
            
            # Test pose saving from all controls
            import maya.cmds as cmds
            
            # Set some attribute values
            cmds.setAttr(f"{test_controls[0]}.smile", 0.5)
            cmds.setAttr(f"{test_controls[1]}.frown", -0.3)
            
            # Save pose from current state
            pose_data = animator.save_pose_from_selection(
                "Integration Test Pose",
                "Pose created during integration testing",
                use_current_selection=False,  # Use all controls
                auto_save_to_file=False
            )
            
            if pose_data:
                logger.info(f"Successfully saved pose: {pose_data.name}")
                logger.info(f"Pose has {pose_data.get_control_count()} controls")
                logger.info(f"Pose has {pose_data.get_attribute_count()} attributes")
            else:
                logger.error("Failed to save pose")
                return 1
                
            # Test pose application
            # Reset attributes first
            animator.reset_all_attributes(mode=ControlSelectionMode.PATTERN)
            
            # Apply the saved pose
            success = animator.apply_saved_pose("Integration Test Pose")
            if success:
                logger.info("Successfully applied saved pose")
            else:
                logger.error("Failed to apply saved pose")
                return 1
            
            logger.info("All integration tests passed!")
            return 0
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
    except Exception as e:
        logger.error(f"Error in integration tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run facial_pose_animator unit tests with mayapy')
    parser.add_argument('test_class', nargs='?', help='Specific test class to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-maya', action='store_true', help='Run without Maya initialization (mocks only)')
    parser.add_argument('--integration', action='store_true', help='Run integration tests with real Maya functionality')
    
    args = parser.parse_args()
    
    print("Facial Pose Animator - Maya Test Runner")
    print("=" * 60)
    
    # Setup test environment
    if not setup_test_environment():
        logger.error("Failed to setup test environment")
        return 1
    
    exit_code = 0
    
    if args.integration:
        # Run integration tests (requires Maya)
        if not setup_maya_environment():
            logger.error("Failed to initialize Maya for integration tests")
            return 1
        exit_code = run_integration_tests()
        
    elif args.no_maya:
        # Run tests without Maya
        logger.info("Running tests in mock mode (no Maya initialization)")
        exit_code = run_tests_without_maya(args.test_class, args.verbose)
        
    else:
        # Try to run with Maya, fallback to mock mode
        if setup_maya_environment():
            exit_code = run_tests_with_maya(args.test_class, args.verbose)
        else:
            logger.warning("Maya initialization failed, falling back to mock mode")
            exit_code = run_tests_without_maya(args.test_class, args.verbose)
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("SOME TESTS FAILED! ✗")
        print("=" * 60)
    
    return exit_code


if __name__ == '__main__':
    # Finalize Maya when script exits
    try:
        exit_code = main()
    finally:
        try:
            import maya.standalone
            maya.standalone.uninitialize()
        except:
            pass  # Ignore cleanup errors
    
    sys.exit(exit_code)