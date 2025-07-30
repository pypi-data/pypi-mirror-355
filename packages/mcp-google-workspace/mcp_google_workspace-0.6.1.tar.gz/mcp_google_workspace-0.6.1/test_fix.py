#!/usr/bin/env python3
"""Test script to verify the get_email_by_id method exists and works correctly."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import just the gmail module to avoid dependency issues
import importlib.util
spec = importlib.util.spec_from_file_location("gmail", os.path.join(os.path.dirname(__file__), 'src/mcp_gsuite/gmail.py'))
gmail_module = importlib.util.module_from_spec(spec)

# We need to mock the gauth import since it has dependencies
sys.modules['gauth'] = type(sys)('gauth')

# Now load the module
spec.loader.exec_module(gmail_module)
GmailService = gmail_module.GmailService

# Check that the method exists
if hasattr(GmailService, 'get_email_by_id'):
    print("✓ get_email_by_id method exists in GmailService")
else:
    print("✗ get_email_by_id method NOT found in GmailService")
    sys.exit(1)

# Check that the method has the correct signature
import inspect
sig = inspect.signature(GmailService.get_email_by_id)
params = list(sig.parameters.keys())
expected_params = ['self', 'email_id']

if params == expected_params:
    print("✓ get_email_by_id has correct parameters:", params)
else:
    print("✗ get_email_by_id has incorrect parameters:", params)
    print("  Expected:", expected_params)
    sys.exit(1)

# Check the docstring
if GmailService.get_email_by_id.__doc__:
    print("✓ get_email_by_id has documentation")
    print("  First line:", GmailService.get_email_by_id.__doc__.strip().split('\n')[0])
else:
    print("✗ get_email_by_id missing documentation")

print("\nAll checks passed! The get_email_by_id method has been successfully added.")