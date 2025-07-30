#!/usr/bin/env python3
"""Test to verify GmailService has get_email_by_id method"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from mcp_gsuite import gmail
    
    # Check if GmailService class exists
    if hasattr(gmail, 'GmailService'):
        print("✓ GmailService class found")
        
        # Check if get_email_by_id method exists
        if hasattr(gmail.GmailService, 'get_email_by_id'):
            print("✓ get_email_by_id method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(gmail.GmailService.get_email_by_id)
            print(f"  Method signature: {sig}")
        else:
            print("✗ get_email_by_id method NOT found")
            print("  Available methods:")
            for attr in dir(gmail.GmailService):
                if not attr.startswith('_') and callable(getattr(gmail.GmailService, attr)):
                    print(f"    - {attr}")
    else:
        print("✗ GmailService class NOT found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()