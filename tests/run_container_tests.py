#!/usr/bin/env python
"""
Container-optimized test runner for facial_pose_animator tests in Maya Docker environment.
"""

import sys
import os
import argparse
import logging

# Configure logging for container environment
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/test_results/test.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def setup_maya_environment():
    """Initialize Maya for headless operation in container."""
    try:
        import maya.standalone
        maya.standalone.initialize(name='python')
        
        # Configure Maya for headless operation
        import maya.cmds as cmds
        
        # Set render globals for faster operation
        cmds.setAttr("defaultRenderGlobals.imageFormat", 8)  # JPEG
        cmds.setAttr("defaultRenderGlobals.animation", 0)     # Single frame
        
        # Disable unnecessary Maya features for testing
        cmds.optionVar(iv=("suppressFileOpenDialog", 1))
        cmds.optionVar(iv=("suppressFileSaveDialog", 1))
        
        logger.info("Maya standalone initialized successfully in container")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Maya: {e}")
        return False

def run_tests(test_class=None, verbose=False, output_dir="/app/test_results"):
    """Run the facial pose animator tests."""
    try:
        # Import test module
        from test_facial_pose_animator import FacialPoseAnimatorTestSuite
        
        logger.info(f"Running tests in Maya container environment")
        if test_class:
            logger.info(f"Target test class: {test_class}")
        
        # Run tests
        suite = FacialPoseAnimatorTestSuite()
        if test_class:
            result = suite.run_specific_test(test_class)
        else:
            result = suite.run_all_tests()
        
        # Write detailed results to file
        results_file = os.path.join(output_dir, "test_results.txt")
        with open(results_file, 'w') as f:
            f.write("Maya Container Test Results\n")
            f.write("=" * 50 + "\n")
            f.write(f"Tests run: {result.testsRun}\n")
            f.write(f"Failures: {len(result.failures)}\n")
            f.write(f"Errors: {len(result.errors)}\n")
            f.write(f"Success: {result.wasSuccessful()}\n\n")
            
            if result.failures:
                f.write("FAILURES:\n")
                f.write("-" * 20 + "\n")
                for i, (test, traceback) in enumerate(result.failures, 1):
                    f.write(f"{i}. {test}\n")
                    f.write(f"{traceback}\n\n")
            
            if result.errors:
                f.write("ERRORS:\n")
                f.write("-" * 20 + "\n")
                for i, (test, traceback) in enumerate(result.errors, 1):
                    f.write(f"{i}. {test}\n")
                    f.write(f"{traceback}\n\n")
        
        # Print summary to stdout
        print("\n" + "=" * 60)
        print("MAYA CONTAINER TEST RESULTS")
        print("=" * 60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success: {result.wasSuccessful()}")
        print(f"Results written to: {results_file}")
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(description='Run facial_pose_animator tests in Maya container')
    parser.add_argument('test_class', nargs='?', help='Specific test class to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output-dir', default='/app/test_results', help='Output directory for test results')
    
    args = parser.parse_args()
    
    print("Facial Pose Animator - Maya Container Test Runner")
    print("=" * 60)
    
    # Initialize Maya
    if not setup_maya_environment():
        logger.error("Failed to initialize Maya environment")
        return 1
    
    # Run tests
    exit_code = run_tests(args.test_class, args.verbose, args.output_dir)
    
    # Cleanup
    try:
        import maya.standalone
        maya.standalone.uninitialize()
        logger.info("Maya environment cleaned up")
    except:
        pass
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())