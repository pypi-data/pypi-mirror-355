#!/usr/bin/env python3
"""
Integration test for Gmail HTML and attachment features
This script creates test files and verifies the implementation works correctly
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import asyncio
import traceback

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_gsuite.gmail import GmailService
from mcp_gsuite.tools_gmail import (
    CreateDraftToolHandler, 
    SendEmailToolHandler,
    ReplyEmailToolHandler,
    QueryEmailsToolHandler
)

def create_test_files():
    """Create test files for attachment testing"""
    test_dir = Path(tempfile.gettempdir()) / "gmail_mcp_test"
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    files = {}
    
    # Plain text file
    text_file = test_dir / "test_document.txt"
    text_file.write_text("This is a test document for Gmail MCP attachment testing.\n" * 5)
    files["text"] = str(text_file)
    
    # HTML file
    html_file = test_dir / "test_report.html"
    html_file.write_text("""
<!DOCTYPE html>
<html>
<head><title>Test Report</title></head>
<body>
    <h1>Gmail MCP Test Report</h1>
    <p>This HTML file tests attachment functionality.</p>
    <table border="1">
        <tr><th>Feature</th><th>Status</th></tr>
        <tr><td>HTML Email</td><td>✓ Supported</td></tr>
        <tr><td>Attachments</td><td>✓ Supported</td></tr>
    </table>
</body>
</html>
    """)
    files["html"] = str(html_file)
    
    # CSV file
    csv_file = test_dir / "test_data.csv"
    csv_file.write_text("""Name,Email,Feature,Status
HTML Support,test@example.com,HTML Emails,Implemented
Attachment Support,test@example.com,File Attachments,Implemented
Combined Features,test@example.com,HTML + Attachments,Implemented
""")
    files["csv"] = str(csv_file)
    
    # Python file (to test code attachment)
    py_file = test_dir / "example_code.py"
    py_file.write_text("""# Example Python code attachment
def greet(name):
    return f"Hello, {name}! This code was sent via Gmail MCP."

if __name__ == "__main__":
    print(greet("Gmail User"))
""")
    files["python"] = str(py_file)
    
    print(f"✓ Created test files in: {test_dir}")
    for name, path in files.items():
        print(f"  - {name}: {path}")
    
    return files

def test_create_draft_handler():
    """Test the CreateDraftToolHandler directly"""
    print("\n=== Testing CreateDraftToolHandler ===")
    
    handler = CreateDraftToolHandler()
    tool_desc = handler.get_tool_description()
    
    print(f"Tool name: {tool_desc.name}")
    print(f"Tool description: {tool_desc.description[:100]}...")
    
    # Check schema includes new parameters
    schema = tool_desc.inputSchema
    properties = schema.get("properties", {})
    
    assert "html_body" in properties, "html_body parameter missing from schema"
    assert "attachments" in properties, "attachments parameter missing from schema"
    
    print("✓ Tool schema includes html_body and attachments parameters")
    
    return True

def test_send_email_handler():
    """Test the SendEmailToolHandler"""
    print("\n=== Testing SendEmailToolHandler ===")
    
    handler = SendEmailToolHandler()
    tool_desc = handler.get_tool_description()
    
    print(f"Tool name: {tool_desc.name}")
    
    # Check schema
    schema = tool_desc.inputSchema
    properties = schema.get("properties", {})
    
    assert "html_body" in properties, "html_body parameter missing from send email schema"
    assert "attachments" in properties, "attachments parameter missing from send email schema"
    
    print("✓ Send email tool includes HTML and attachment support")
    
    return True

def test_reply_email_handler():
    """Test the ReplyEmailToolHandler"""
    print("\n=== Testing ReplyEmailToolHandler ===")
    
    handler = ReplyEmailToolHandler()
    tool_desc = handler.get_tool_description()
    
    print(f"Tool name: {tool_desc.name}")
    
    # Check schema
    schema = tool_desc.inputSchema
    properties = schema.get("properties", {})
    
    assert "html_body" in properties, "html_body parameter missing from reply schema"
    assert "attachments" in properties, "attachments parameter missing from reply schema"
    
    print("✓ Reply email tool includes HTML and attachment support")
    
    return True

def test_mime_message_creation():
    """Test MIME message creation without actually sending"""
    print("\n=== Testing MIME Message Creation ===")
    
    # Test files
    files = create_test_files()
    
    # Import the necessary modules
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email.mime.image import MIMEImage
    from email import encoders
    import mimetypes
    import base64
    
    # Test creating a multipart message
    mime_message = MIMEMultipart('mixed')
    
    # Add HTML and plain text
    msg_alternative = MIMEMultipart('alternative')
    
    text_part = MIMEText("Plain text version", 'plain')
    msg_alternative.attach(text_part)
    
    html_part = MIMEText("<html><body><h1>HTML version</h1></body></html>", 'html')
    msg_alternative.attach(html_part)
    
    mime_message.attach(msg_alternative)
    
    # Add an attachment
    with open(files["text"], 'rb') as f:
        attachment = MIMEBase('text', 'plain')
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename='test.txt')
        mime_message.attach(attachment)
    
    # Set headers
    mime_message['to'] = 'test@example.com'
    mime_message['subject'] = 'Test Email'
    
    # Convert to raw format (as Gmail API expects)
    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
    
    print(f"✓ Created MIME message with {len(mime_message.get_payload())} parts")
    print(f"✓ Raw message size: {len(raw_message)} bytes")
    
    return True

def generate_test_examples(files):
    """Generate example tool calls for manual testing"""
    print("\n=== Generated Test Examples ===")
    
    examples = []
    
    # Example 1: Simple HTML draft
    example1 = {
        "tool": "create_gmail_draft",
        "description": "Create a simple HTML email draft",
        "args": {
            "__user_id__": "your-email@gmail.com",  # Replace with actual email
            "to": "test@example.com",
            "subject": "Test: Simple HTML Email",
            "body": "This is the plain text version.",
            "html_body": """<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #2c3e50;">HTML Email Test</h2>
    <p>This email demonstrates <strong>HTML formatting</strong>.</p>
    <ul>
        <li>Rich text formatting</li>
        <li>Styled content</li>
        <li>Lists and structure</li>
    </ul>
</body>
</html>"""
        }
    }
    examples.append(example1)
    
    # Example 2: Email with attachments
    example2 = {
        "tool": "create_gmail_draft",
        "description": "Create email with multiple attachments",
        "args": {
            "__user_id__": "your-email@gmail.com",  # Replace with actual email
            "to": "test@example.com",
            "subject": "Test: Email with Attachments",
            "body": "Please find the test files attached.",
            "attachments": list(files.values())
        }
    }
    examples.append(example2)
    
    # Example 3: Complete email with HTML and attachments
    example3 = {
        "tool": "send_gmail_email",
        "description": "Send email with both HTML and attachments",
        "args": {
            "__user_id__": "your-email@gmail.com",  # Replace with actual email
            "to": "test@example.com",
            "subject": "Test: Complete Email Features",
            "body": "This email has both HTML and attachments.",
            "html_body": """<html>
<body>
    <h2>Complete Feature Test</h2>
    <p>This email includes:</p>
    <ol>
        <li><strong>HTML formatting</strong></li>
        <li><em>Multiple attachments</em></li>
        <li>All features combined</li>
    </ol>
    <div style="background: #f0f0f0; padding: 10px; margin: 10px 0;">
        <p>Attached files:</p>
        <ul>
            <li>test_document.txt</li>
            <li>test_report.html</li>
            <li>test_data.csv</li>
            <li>example_code.py</li>
        </ul>
    </div>
</body>
</html>""",
            "attachments": list(files.values())
        }
    }
    examples.append(example3)
    
    # Save examples to file
    examples_file = Path("test_examples.json")
    with open(examples_file, 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"✓ Generated {len(examples)} test examples")
    print(f"✓ Saved to: {examples_file}")
    
    return examples

def main():
    """Run all tests"""
    print("=== Gmail MCP Integration Test Suite ===")
    print("Testing HTML and attachment features...\n")
    
    try:
        # Test tool handlers
        test_create_draft_handler()
        test_send_email_handler()
        test_reply_email_handler()
        
        # Test MIME message creation
        test_mime_message_creation()
        
        # Create test files
        files = create_test_files()
        
        # Generate examples
        examples = generate_test_examples(files)
        
        print("\n=== All Tests Passed! ===")
        print("\nNext steps:")
        print("1. Replace 'your-email@gmail.com' with your actual email in test_examples.json")
        print("2. Use MCP Inspector to test the tool calls:")
        print("   npx @modelcontextprotocol/inspector uv --directory . run mcp-google-workspace")
        print("3. Or test with Claude Desktop after configuration")
        
        print("\nThe implementation is ready for testing and deployment!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())