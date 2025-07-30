# Enhanced Gmail Features

This document describes the enhanced Gmail features added to the mcp-google-workspace server.

## HTML Email Support

Both `create_gmail_draft` and `reply_gmail_email` tools now support HTML formatting:

### Creating HTML Drafts

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "recipient@example.com",
  "subject": "HTML Email Example",
  "body": "This is the plain text version",
  "html_body": "<html><body><h1>HTML Email</h1><p>This is <strong>HTML</strong> content.</p></body></html>"
}
```

### Benefits:
- Rich text formatting (bold, italic, colors)
- Tables and structured layouts
- Embedded images and styling
- Professional email templates

## File Attachment Support

You can now attach files to drafts and emails:

### Attaching Files

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "recipient@example.com",
  "subject": "Email with Attachments",
  "body": "Please find the attached files.",
  "attachments": [
    "/path/to/document.pdf",
    "/path/to/image.jpg",
    "/path/to/spreadsheet.xlsx"
  ]
}
```

### Supported Features:
- Multiple file attachments
- Automatic MIME type detection
- Support for all common file types
- Proper encoding for email transmission

## New Send Email Tool

A new `send_gmail_email` tool allows sending emails immediately (not as drafts):

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "recipient@example.com",
  "subject": "Direct Send",
  "body": "This email is sent immediately",
  "html_body": "<html><body><p>With <em>HTML</em> support!</p></body></html>",
  "attachments": ["/path/to/file.pdf"]
}
```

## Enhanced Reply Functionality

The `reply_gmail_email` tool now also supports HTML and attachments:

```json
{
  "__user_id__": "your-email@gmail.com",
  "original_message_id": "message-id-here",
  "reply_body": "Thanks for your email!",
  "html_body": "<html><body><p>Thanks for your <strong>email</strong>!</p></body></html>",
  "attachments": ["/path/to/response-doc.pdf"],
  "send": false
}
```

## Technical Implementation

### MIME Structure
- Uses `multipart/mixed` for emails with attachments
- Uses `multipart/alternative` for HTML/plain text alternatives
- Proper nesting of MIME parts for complex emails

### File Handling
- Files are read from the local filesystem
- Base64 encoding for email transmission
- Automatic content-type detection using Python's `mimetypes` module

### Error Handling
- Graceful handling of missing files
- Warnings logged for attachment errors
- Email still sent if some attachments fail

## Examples

### Professional Newsletter
```json
{
  "__user_id__": "newsletter@company.com",
  "to": "subscribers@list.com",
  "subject": "Monthly Newsletter - December 2024",
  "body": "View this email in HTML for the best experience.",
  "html_body": "<html><body style='font-family: Arial;'><div style='background: #f0f0f0; padding: 20px;'><h1>Company Newsletter</h1><p>Latest updates...</p></div></body></html>",
  "attachments": [
    "/path/to/newsletter-images/header.png",
    "/path/to/reports/monthly-summary.pdf"
  ]
}
```

### Job Application
```json
{
  "__user_id__": "applicant@gmail.com",
  "to": "hr@company.com",
  "subject": "Application for Software Engineer Position",
  "body": "Please find my application attached.",
  "html_body": "<html><body><p>Dear Hiring Manager,</p><p>I am writing to apply for the <strong>Software Engineer</strong> position...</p></body></html>",
  "attachments": [
    "/path/to/resume.pdf",
    "/path/to/cover-letter.pdf",
    "/path/to/portfolio.pdf"
  ]
}
```

## Best Practices

1. **Always include plain text**: Even when sending HTML emails, include a plain text version for compatibility
2. **Test attachments**: Verify file paths exist before sending
3. **File size limits**: Gmail has a 25MB limit for attachments
4. **HTML compatibility**: Use simple HTML that works across email clients
5. **Security**: Never attach sensitive files without encryption