# Changelog

All notable changes to mcp-google-workspace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.4] - 2025-01-06

### Added
- Comprehensive documentation for HTML email and attachment features
- USAGE_GUIDE.md with detailed examples and best practices
- Integration test suite for verifying functionality
- Test example generator for easy testing

### Enhanced
- Documentation in README.md now clearly lists HTML and attachment support
- Added more detailed examples in ENHANCED_FEATURES.md

### Technical
- HTML email support via `html_body` parameter in create_gmail_draft, send_gmail_email, and reply_gmail_email
- File attachment support via `attachments` parameter accepting list of file paths
- Automatic MIME type detection for attachments
- Proper multipart/alternative and multipart/mixed MIME structure

## [0.5.3] - 2025-01-05

### Fixed
- Various bug fixes and improvements

## [0.5.2] - 2025-01-04

### Added
- New send_gmail_email tool for sending emails directly (not as drafts)

## [0.5.1] - 2025-01-03

### Added
- Email retrieval by ID functionality
- New dependencies: aiohttp, packaging

## [0.5.0] - 2025-01-02

### Changed
- Renamed project from mcp-gsuite to mcp-google-workspace
- Updated all references and configuration files

## [0.4.x] - Previous versions

### Added
- Initial Gmail and Google Calendar integration
- OAuth2 authentication flow
- Multi-account support
- Basic email operations (query, read, draft, delete)
- Calendar event management