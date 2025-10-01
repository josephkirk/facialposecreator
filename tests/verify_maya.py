#!/usr/bin/env python
"""
Simple Maya verification script for container environment.
"""
import maya.standalone
maya.standalone.initialize(name='python')

import maya.cmds as cmds
print("Maya version:", cmds.about(version=True))
print("Maya batch mode:", cmds.about(batch=True))

# Create a simple object to verify Maya is working
cube = cmds.polyCube(name='test_cube')[0]
print(f"Created test object: {cube}")

# Clean up
cmds.delete(cube)
print("Maya verification successful!")

maya.standalone.uninitialize()