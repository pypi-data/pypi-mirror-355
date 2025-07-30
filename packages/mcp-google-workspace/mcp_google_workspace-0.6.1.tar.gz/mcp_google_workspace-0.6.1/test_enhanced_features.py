#!/usr/bin/env python3
"""
Test script for enhanced Gmail features (HTML and attachments)

This script demonstrates:
1. Creating drafts with HTML formatting
2. Attaching files to emails
3. Sending emails directly with attachments
4. Replying to emails with HTML and attachments
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path

# Create test files for attachments
def create_test_files():
    """Create sample files to use as attachments"""
    test_dir = Path(tempfile.gettempdir()) / "gmail_test_attachments"
    test_dir.mkdir(exist_ok=True)
    
    # Create a text file
    text_file = test_dir / "test_document.txt"
    text_file.write_text("This is a test document for Gmail attachment testing.\n" * 10)
    
    # Create an HTML file
    html_file = test_dir / "test_report.html"
    html_file.write_text("""
    <html>
    <head><title>Test Report</title></head>
    <body>
        <h1>Test Report</h1>
        <p>This is a test HTML report for attachment testing.</p>
        <table border="1">
            <tr><th>Test</th><th>Result</th></tr>
            <tr><td>HTML Support</td><td>✓ Passed</td></tr>
            <tr><td>Attachment Support</td><td>✓ Passed</td></tr>
        </table>
    </body>
    </html>
    """)
    
    # Create a simple CSV file
    csv_file = test_dir / "test_data.csv"
    csv_file.write_text("Name,Email,Status\nJohn Doe,john@example.com,Active\nJane Smith,jane@example.com,Active\n")
    
    return {
        "text": str(text_file),
        "html": str(html_file),
        "csv": str(csv_file)
    }

def test_create_draft_with_html():
    """Test creating a draft with HTML content"""
    print("\n=== Testing Draft Creation with HTML ===")
    
    test_data = {
        "__user_id__": "test@example.com",  # Replace with actual email
        "to": "recipient@example.com",
        "subject": "Test: HTML Email Draft",
        "body": "This is the plain text version of the email.",
        "html_body": """
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #2c3e50;">HTML Email Test</h2>
            <p>This email demonstrates <strong>HTML formatting</strong> capabilities:</p>
            <ul>
                <li>✓ <em>Rich text formatting</em></li>
                <li>✓ <span style="color: #e74c3c;">Colored text</span></li>
                <li>✓ <a href="https://example.com">Hyperlinks</a></li>
            </ul>
            <div style="background-color: #ecf0f1; padding: 10px; border-radius: 5px;">
                <p>This is a styled div with background color.</p>
            </div>
        </body>
        </html>
        """
    }
    
    print("Draft data:", json.dumps(test_data, indent=2))
    return test_data

def test_create_draft_with_attachments(file_paths):
    """Test creating a draft with file attachments"""
    print("\n=== Testing Draft Creation with Attachments ===")
    
    test_data = {
        "__user_id__": "test@example.com",  # Replace with actual email
        "to": "recipient@example.com",
        "subject": "Test: Email with Attachments",
        "body": "Please find the attached test files.",
        "attachments": list(file_paths.values())
    }
    
    print("Draft data:", json.dumps(test_data, indent=2))
    return test_data

def test_send_email_with_both(file_paths):
    """Test sending an email with both HTML and attachments"""
    print("\n=== Testing Send Email with HTML and Attachments ===")
    
    test_data = {
        "__user_id__": "test@example.com",  # Replace with actual email
        "to": "recipient@example.com",
        "subject": "Test: Complete Email with HTML and Attachments",
        "body": "This is the plain text fallback version.",
        "html_body": """
        <html>
        <body>
            <h2>Complete Email Test</h2>
            <p>This email includes both <strong>HTML formatting</strong> and <em>file attachments</em>.</p>
            <h3>Attached Files:</h3>
            <ol>
                <li>test_document.txt - A text document</li>
                <li>test_report.html - An HTML report</li>
                <li>test_data.csv - Sample CSV data</li>
            </ol>
            <p style="color: #7f8c8d; font-size: 12px;">This email was created using the enhanced Gmail MCP tools.</p>
        </body>
        </html>
        """,
        "attachments": list(file_paths.values())
    }
    
    print("Email data:", json.dumps(test_data, indent=2))
    return test_data

def test_reply_with_enhancements(file_paths):
    """Test replying to an email with HTML and attachments"""
    print("\n=== Testing Reply with HTML and Attachments ===")
    
    test_data = {
        "__user_id__": "test@example.com",  # Replace with actual email
        "original_message_id": "REPLACE_WITH_ACTUAL_MESSAGE_ID",
        "reply_body": "Thank you for your email. Please see my response below.",
        "html_body": """
        <html>
        <body>
            <p>Thank you for your email. Please see my response below.</p>
            <div style="border-left: 3px solid #3498db; padding-left: 10px; margin: 10px 0;">
                <h3>Response Summary:</h3>
                <ul>
                    <li>✓ Reviewed your request</li>
                    <li>✓ Prepared the requested documents</li>
                    <li>✓ Attached relevant files</li>
                </ul>
            </div>
            <p>Please let me know if you need any additional information.</p>
            <p style="color: #7f8c8d;">Best regards,<br>Test User</p>
        </body>
        </html>
        """,
        "attachments": [file_paths["csv"]],  # Just attach the CSV as an example
        "send": False  # Save as draft
    }
    
    print("Reply data:", json.dumps(test_data, indent=2))
    return test_data

def main():
    """Run all tests"""
    print("=== Gmail Enhanced Features Test Suite ===")
    print("\nThis script demonstrates the HTML and attachment capabilities.")
    print("NOTE: Replace 'test@example.com' with your actual email address in the test data.")
    print("NOTE: For reply test, you'll need an actual message ID from your inbox.")
    
    # Create test files
    print("\nCreating test files...")
    file_paths = create_test_files()
    print(f"Created test files in: {Path(tempfile.gettempdir()) / 'gmail_test_attachments'}")
    for name, path in file_paths.items():
        print(f"  - {name}: {path}")
    
    # Run tests
    test_create_draft_with_html()
    test_create_draft_with_attachments(file_paths)
    test_send_email_with_both(file_paths)
    test_reply_with_enhancements(file_paths)
    
    print("\n=== Test Examples Complete ===")
    print("\nTo use these examples:")
    print("1. Replace 'test@example.com' with your actual email address")
    print("2. Use the MCP Inspector or Claude Desktop to execute these tool calls")
    print("3. For the reply test, first query your emails to get a valid message ID")
    print("\nThe test files have been created and can be used for actual testing.")

if __name__ == "__main__":
    main()