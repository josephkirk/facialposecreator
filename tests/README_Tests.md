# Facial Pose Animator - Unit Test Suite

This directory contains comprehensive unit tests for the `facial_pose_animator.py` module, designed to work both with Maya's Python environment (mayapy) and with mocked dependencies for standalone testing.

## Files Overview

### Core Files
- **`facial_pose_animator.py`** - Main module being tested
- **`test_facial_pose_animator.py`** - Comprehensive unit test suite
- **`run_tests_with_mayapy.py`** - Python test runner script for mayapy
- **`run_tests.bat`** - Windows batch script for easy test execution
- **`run_tests.ps1`** - PowerShell script for cross-platform support
- **`README.md`** - This documentation file

## Test Coverage

The test suite covers all major components of the facial pose animator:

### 1. FacialPoseData Class Tests (`TestFacialPoseData`)
- Dataclass initialization and validation
- Dictionary serialization (`to_dict`, `from_dict`)
- Pose validation (`is_valid`)
- Control and attribute counting
- Control existence checking
- Attribute name sanitization

### 2. Enum and Exception Tests
- `ControlSelectionMode` enum values
- Custom exception class hierarchy and inheritance
- Exception raising and handling

### 3. FacialPoseAnimator Initialization (`TestFacialPoseAnimatorInitialization`)
- Default settings and configuration
- Control validation (`_is_valid_control`)
- Attribute validation (`_is_valid_attribute`)
- Scene setup validation
- Selection mode configuration

### 4. Control Selection Methods (`TestControlSelection`)
- Pattern-based control selection
- Maya selection-based control selection
- Object set-based control selection
- Metadata-based control selection
- Fallback mechanisms and error handling

### 5. Pose Management (`TestPoseManagement`)
- Saving poses from selection or all controls
- Applying saved poses with blend factors
- Listing and removing saved poses
- Pose comparison functionality
- Pose validation and error handling

### 6. File I/O Operations (`TestFileOperations`)
- Exporting poses to JSON files
- Importing poses from JSON files
- Single pose file operations
- Pose name file writing
- Directory and file path handling

### 7. Undo/Cleanup Tracking (`TestUndoTracking`)
- Node, connection, and attribute tracking
- Cleanup operations and error handling
- Undo tracking enable/disable functionality

### 8. Convenience Functions (`TestConvenienceFunctions`)
- Factory functions for animator creation
- Quick utility functions for common operations
- Wrapper functions with error handling

### 9. Maya Operations with Mocking (`TestMayaOperationsMocked`)
- Maya scene operations with proper mocking
- PyMEL function calls and return values
- Maya-specific error conditions

## Running the Tests

### Option 1: Automatic Test Runner (Recommended)

#### Windows Batch Script
```cmd
# Run all tests
run_tests.bat

# Run specific test class
run_tests.bat TestFacialPoseData

# Run integration tests with real Maya
run_tests.bat --integration

# Run mock tests only (no Maya required)
run_tests.bat --no-maya
```

#### PowerShell Script
```powershell
# Run all tests
.\run_tests.ps1

# Run specific test class with verbose output
.\run_tests.ps1 TestPoseManagement -Verbose

# Run integration tests
.\run_tests.ps1 -Integration

# Run mock tests only
.\run_tests.ps1 -NoMaya
```

### Option 2: Direct mayapy Execution

If you have Maya installed and want to run tests directly:

```cmd
# Run all tests
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" run_tests_with_mayapy.py

# Run specific test class
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" run_tests_with_mayapy.py TestFacialPoseData

# Run with verbose output
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" run_tests_with_mayapy.py --verbose

# Run integration tests (creates real Maya scene)
"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" run_tests_with_mayapy.py --integration
```

### Option 3: Standard Python (Mock Mode Only)

For testing without Maya (uses mocked PyMEL):

```cmd
python run_tests_with_mayapy.py --no-maya
python test_facial_pose_animator.py
```

## Test Modes Explained

### 1. Mock Mode (Default without Maya)
- Uses `unittest.mock` to simulate PyMEL and Maya functionality
- Tests all logic and error handling without requiring Maya
- Fast execution and suitable for CI/CD pipelines
- Automatically used when Maya is not available

### 2. Maya Environment Mode
- Uses real PyMEL and Maya functionality
- Tests actual Maya integration and behavior
- Requires Maya installation and mayapy.exe
- More comprehensive but slower execution

### 3. Integration Mode
- Creates real Maya scene with test controls
- Tests end-to-end functionality with actual Maya operations
- Validates real-world usage scenarios
- Use with `--integration` flag

## Expected Output

### Successful Test Run
```
Facial Pose Animator - Maya Test Runner
============================================================
INFO: Maya standalone environment initialized successfully
INFO: Test module imported successfully
INFO: Running all test classes

test_initialization (test_facial_pose_animator.TestFacialPoseData) ... ok
test_to_dict (test_facial_pose_animator.TestFacialPoseData) ... ok
test_from_dict (test_facial_pose_animator.TestFacialPoseData) ... ok
...

============================================================
MAYA ENVIRONMENT TEST RESULTS  
============================================================
Tests run: 89
Failures: 0
Errors: 0
Success: True

============================================================
ALL TESTS COMPLETED SUCCESSFULLY! ✓
============================================================
```

### Failed Test Example
```
FAILURES:
1. test_save_pose_from_selection (test_facial_pose_animator.TestPoseManagement)
----------------------------------------
Traceback (most recent call last):
  File "test_facial_pose_animator.py", line 450, in test_save_pose_from_selection
    self.assertEqual(result.name, "New Pose")
AssertionError: 'Test Pose' != 'New Pose'
```

## Troubleshooting

### Common Issues

1. **"Failed to import Maya modules"**
   - Ensure you're using mayapy.exe, not regular Python
   - Check Maya installation path
   - Use `--no-maya` flag for mock testing

2. **"Test module imported successfully" but tests fail**
   - Check that `facial_pose_animator.py` is in the same directory
   - Verify all dependencies are available
   - Run with `--verbose` for detailed output

3. **Integration tests fail**
   - Make sure Maya can create new scenes
   - Check Maya licensing (some operations require full license)
   - Verify Maya preferences and startup scripts

### Debugging Tips

1. **Enable verbose output**: Add `--verbose` or `-v` flag
2. **Run specific test classes**: Focus on failing areas
3. **Check file permissions**: Ensure test files can be created/modified
4. **Maya environment**: Run `mayapy.exe` interactively to test Maya setup

## Extending the Tests

### Adding New Test Cases

1. **Create new test class**:
```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.animator = FacialPoseAnimator()
    
    def test_new_functionality(self):
        # Your test code here
        pass
```

2. **Add to test suite**:
```python
# In FacialPoseAnimatorTestSuite.run_all_tests()
test_classes = [
    # ... existing classes
    TestNewFeature,  # Add your new class
]
```

### Mocking Guidelines

When mocking Maya/PyMEL functionality:

```python
@patch('facial_pose_animator.pm')
def test_maya_operation(self, mock_pm):
    # Configure mock behavior
    mock_pm.ls.return_value = [MockPyNode("test")]
    
    # Test your functionality
    result = self.animator.some_method()
    
    # Verify mock was called correctly
    mock_pm.ls.assert_called_with("pattern", type='transform')
```

## Performance Considerations

- **Mock tests**: Very fast (~2-5 seconds for full suite)
- **Maya environment tests**: Moderate (~30-60 seconds for full suite)  
- **Integration tests**: Slower (~2-5 minutes, creates real Maya scenes)

For development, use mock mode for quick iteration, and run Maya environment tests before committing changes.

## Continuous Integration

The test suite is designed to work in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Facial Pose Animator Tests
  run: |
    python run_tests_with_mayapy.py --no-maya --verbose
```

Use `--no-maya` flag in CI since Maya typically isn't available in CI environments.

## Contributing

When contributing new features to `facial_pose_animator.py`:

1. Add corresponding unit tests in `test_facial_pose_animator.py`
2. Ensure all tests pass in both mock and Maya modes
3. Add integration tests for complex Maya-dependent features
4. Update this README if new test categories are added

## License

This test suite follows the same license as the main `facial_pose_animator.py` module.