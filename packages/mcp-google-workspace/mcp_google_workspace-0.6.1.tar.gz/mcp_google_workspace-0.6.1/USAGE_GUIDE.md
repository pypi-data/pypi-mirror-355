# Gmail Enhanced Features Usage Guide

This guide provides detailed examples of using the HTML formatting and file attachment features in the mcp-google-workspace server.

## Table of Contents
1. [HTML Email Formatting](#html-email-formatting)
2. [File Attachments](#file-attachments)
3. [Combined Features](#combined-features)
4. [Common Use Cases](#common-use-cases)
5. [Troubleshooting](#troubleshooting)

## HTML Email Formatting

### Basic HTML Email

To create an email with HTML formatting, use the `html_body` parameter:

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "recipient@example.com",
  "subject": "Welcome to Our Service",
  "body": "Welcome! This email looks better in HTML.",
  "html_body": "<html><body><h1>Welcome!</h1><p>We're excited to have you.</p></body></html>"
}
```

### Advanced HTML Formatting

You can use CSS styles, tables, images, and more:

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "team@example.com",
  "subject": "Weekly Report",
  "body": "Weekly report attached.",
  "html_body": "<html><head><style>body { font-family: Arial; } .highlight { background: #ffffcc; } table { border-collapse: collapse; } td, th { border: 1px solid #ddd; padding: 8px; }</style></head><body><h2>Weekly Report</h2><p class='highlight'>Key Metrics:</p><table><tr><th>Metric</th><th>Value</th><th>Change</th></tr><tr><td>Sales</td><td>$45,000</td><td style='color: green;'>+15%</td></tr><tr><td>Users</td><td>1,250</td><td style='color: green;'>+8%</td></tr></table></body></html>"
}
```

## File Attachments

### Single File Attachment

Attach a single file by providing its absolute path:

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "hr@example.com",
  "subject": "Resume Submission",
  "body": "Please find my resume attached.",
  "attachments": ["/Users/yourname/Documents/resume.pdf"]
}
```

### Multiple File Attachments

Attach multiple files by providing an array of paths:

```json
{
  "__user_id__": "your-email@gmail.com",
  "to": "client@example.com",
  "subject": "Project Deliverables",
  "body": "All project files are attached.",
  "attachments": [
    "/path/to/project_report.pdf",
    "/path/to/financial_analysis.xlsx",
    "/path/to/presentation.pptx",
    "/path/to/demo_video.mp4"
  ]
}
```

### Supported File Types

The system automatically detects MIME types for common file formats:
- Documents: PDF, DOC, DOCX, TXT, RTF
- Spreadsheets: XLS, XLSX, CSV
- Images: JPG, PNG, GIF, BMP, SVG
- Archives: ZIP, RAR, TAR, GZ
- Code: PY, JS, HTML, CSS, JSON, XML
- Media: MP3, MP4, AVI, MOV

## Combined Features

### Professional Email with HTML and Attachments

```json
{
  "__user_id__": "sales@company.com",
  "to": "prospect@client.com",
  "subject": "Proposal for Your Review",
  "body": "Please find our proposal attached. This email is best viewed in HTML.",
  "html_body": "<html><body style='font-family: Georgia, serif; line-height: 1.6; color: #333;'><div style='max-width: 600px; margin: 0 auto;'><img src='https://company.com/logo.png' alt='Company Logo' style='width: 200px;'><h2 style='color: #2c3e50;'>Thank You for Your Interest</h2><p>Dear Client,</p><p>We're pleased to present our proposal for your upcoming project. We've carefully reviewed your requirements and prepared a comprehensive solution.</p><div style='background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;'><h3 style='margin-top: 0;'>Proposal Highlights:</h3><ul style='list-style-type: none; padding-left: 0;'><li>✅ Complete project timeline</li><li>✅ Detailed cost breakdown</li><li>✅ Team member profiles</li><li>✅ Case studies</li></ul></div><p>Please review the attached documents and let us know if you have any questions.</p><p style='margin-top: 30px;'>Best regards,<br><strong>Sales Team</strong><br>Company Name<br>sales@company.com | (555) 123-4567</p></div></body></html>",
  "attachments": [
    "/path/to/proposal.pdf",
    "/path/to/cost_breakdown.xlsx",
    "/path/to/case_studies.pdf"
  ]
}
```

## Common Use Cases

### 1. Newsletter with Images

While you can't embed images directly in the email, you can attach them and reference them in your HTML:

```json
{
  "__user_id__": "newsletter@company.com",
  "to": "subscribers@list.com",
  "subject": "Monthly Newsletter - December 2024",
  "body": "View this email in HTML for the best experience.",
  "html_body": "<html><body><h1>Company Newsletter</h1><p>Welcome to our December edition!</p><h2>In This Issue:</h2><ul><li>Year in Review</li><li>Upcoming Events</li><li>Team Spotlight</li></ul><p><em>Images attached to this email</em></p></body></html>",
  "attachments": [
    "/path/to/newsletter_header.png",
    "/path/to/team_photo.jpg",
    "/path/to/infographic.png"
  ]
}
```

### 2. Invoice Email

```json
{
  "__user_id__": "billing@company.com",
  "to": "client@example.com",
  "subject": "Invoice #2024-1234",
  "body": "Invoice attached.",
  "html_body": "<html><body><h2>Invoice #2024-1234</h2><p>Dear Client,</p><p>Please find attached the invoice for services rendered in November 2024.</p><table style='margin: 20px 0;'><tr><td><strong>Invoice Number:</strong></td><td>2024-1234</td></tr><tr><td><strong>Date:</strong></td><td>December 1, 2024</td></tr><tr><td><strong>Amount Due:</strong></td><td>$5,000.00</td></tr><tr><td><strong>Due Date:</strong></td><td>December 31, 2024</td></tr></table><p>Payment instructions are included in the attached invoice.</p><p>Thank you for your business!</p></body></html>",
  "attachments": ["/path/to/invoice_2024_1234.pdf"]
}
```

### 3. Job Application

```json
{
  "__user_id__": "applicant@gmail.com",
  "to": "careers@techcompany.com",
  "subject": "Application for Senior Developer Position",
  "body": "Please find my application materials attached.",
  "html_body": "<html><body style='font-family: Calibri, sans-serif;'><p>Dear Hiring Manager,</p><p>I am writing to express my strong interest in the <strong>Senior Developer</strong> position at TechCompany. With over 8 years of experience in full-stack development and a proven track record of delivering scalable solutions, I am confident I would be a valuable addition to your team.</p><h3>Why I'm a Great Fit:</h3><ul><li>Extensive experience with React, Node.js, and cloud architectures</li><li>Led teams of 5+ developers on multiple successful projects</li><li>Strong focus on code quality and best practices</li></ul><p>I have attached my resume, cover letter, and a portfolio showcasing my recent projects. I would welcome the opportunity to discuss how my skills align with your needs.</p><p>Thank you for your consideration.</p><p>Best regards,<br>John Developer<br>john.developer@gmail.com<br>(555) 987-6543</p></body></html>",
  "attachments": [
    "/path/to/resume.pdf",
    "/path/to/cover_letter.pdf",
    "/path/to/portfolio.pdf"
  ]
}
```

## Troubleshooting

### Common Issues and Solutions

1. **Attachments Not Working**
   - Ensure file paths are absolute (not relative)
   - Verify files exist and are readable
   - Check file permissions
   - Maximum attachment size is 25MB per Gmail limits

2. **HTML Not Rendering**
   - Always include a plain text version in the `body` parameter
   - Use simple, email-compatible HTML
   - Avoid JavaScript and complex CSS
   - Test with different email clients

3. **File Path Examples**
   - macOS: `/Users/username/Documents/file.pdf`
   - Windows: `C:\\Users\\username\\Documents\\file.pdf`
   - Linux: `/home/username/documents/file.pdf`

### Best Practices

1. **Always Include Plain Text**: Some email clients don't support HTML
2. **Keep HTML Simple**: Email HTML rendering varies by client
3. **Test Attachments**: Verify file sizes and paths before sending
4. **Use Proper MIME Types**: The system auto-detects, but unusual files may need attention
5. **Consider File Sizes**: Large attachments may bounce or be rejected

## Tool Reference

### create_gmail_draft
Creates a draft email with optional HTML and attachments.

### send_gmail_email
Sends an email immediately with optional HTML and attachments.

### reply_gmail_email
Creates a reply (draft or sent) with optional HTML and attachments.

All three tools support the same `html_body` and `attachments` parameters, making it easy to use these features consistently across different email operations.