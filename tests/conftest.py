"""
Fix for Python import path issues in tests

This module ensures that the project root is properly added to the Python path
for all tests, allowing proper imports of the agent modules.
"""

import os
import sys

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add project root to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
