from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from . import gmail
import json
from . import toolhandler
import base64

def decode_base64_data(file_data):
    standard_base64_data = file_data.replace("-", "+").replace("_", "/")
    missing_padding = len(standard_base64_data) % 4
    if missing_padding:
        standard_base64_data += '=' * (4 - missing_padding)
    return base64.b64decode(standard_base64_data, validate=True)

class QueryEmailsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("query_gmail_emails")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Query Gmail emails based on an optional search query. 
            Returns emails in reverse chronological order (newest first).
            Returns metadata such as subject and also a short summary of the content.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "query": {
                        "type": "string",
                        "description": """Gmail search query (optional). Examples:
                            - a $string: Search email body, subject, and sender information for $string
                            - 'is:unread' for unread emails
                            - 'from:example@gmail.com' for emails from a specific sender
                            - 'newer_than:2d' for emails from last 2 days
                            - 'has:attachment' for emails with attachments
                            If not provided, returns recent emails without filtering."""
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to retrieve (1-500)",
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": [toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        query = args.get('query')
        max_results = args.get('max_results', 100)
        emails = gmail_service.query_emails(query=query, max_results=max_results)

        return [
            TextContent(
                type="text",
                text=json.dumps(emails, indent=2)
            )
        ]

class GetEmailByIdToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_gmail_email")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves a complete Gmail email message by its ID, including the full message body and attachment IDs.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "email_id": {
                        "type": "string",
                        "description": "The ID of the Gmail message to retrieve"
                    }
                },
                "required": ["email_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "email_id" not in args:
            raise RuntimeError("Missing required argument: email_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        email = gmail_service.get_email_by_id(email_id=args["email_id"])
        
        if email is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to retrieve email with ID: {args['email_id']}"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(email, indent=2)
            )
        ]

class BulkGetEmailsByIdsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("bulk_get_gmail_emails")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves multiple Gmail email messages by their IDs in a single request, including full message bodies.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "email_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Array of Gmail message IDs to retrieve",
                        "minItems": 1,
                        "maxItems": 100
                    }
                },
                "required": ["email_ids", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "email_ids" not in args:
            raise RuntimeError("Missing required argument: email_ids")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        email_ids = args["email_ids"]
        
        emails = []
        for email_id in email_ids:
            email = gmail_service.get_email_by_id(email_id=email_id)
            if email:
                emails.append(email)
            else:
                emails.append({
                    "id": email_id,
                    "error": "Failed to retrieve email"
                })

        return [
            TextContent(
                type="text",
                text=json.dumps(emails, indent=2)
            )
        ]

class CreateDraftToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_gmail_draft")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Creates a draft email message in Gmail with support for plain text, HTML formatting, and file attachments.
            
            The tool supports:
            - Plain text emails (body parameter only)
            - HTML formatted emails (both body and html_body parameters)
            - File attachments (list of file paths)
            - CC recipients
            
            When providing both body and html_body, the email will be sent as multipart/alternative,
            allowing email clients to display the appropriate version.
            
            File attachments should be provided as absolute paths to files on the local filesystem.
            The tool will automatically detect MIME types and encode files appropriately.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "to": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text body content of the email"
                    },
                    "cc": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of email addresses to CC"
                    },
                    "html_body": {
                        "type": "string",
                        "description": "Optional HTML version of the email body. If provided, the email will be sent as multipart/alternative with both plain text and HTML versions."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of file paths to attach to the email. Each path should be an absolute path to a file on the local filesystem."
                    }
                },
                "required": ["to", "subject", "body", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["to", "subject", "body"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        draft = gmail_service.create_draft(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
            cc=args.get("cc"),
            html_body=args.get("html_body"),
            attachments=args.get("attachments")
        )
        
        if draft is None:
            return [
                TextContent(
                    type="text",
                    text="Failed to create draft"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(draft, indent=2)
            )
        ]

class DeleteDraftToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("delete_gmail_draft")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Deletes a draft email message from Gmail by its draft ID.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "draft_id": {
                        "type": "string",
                        "description": "The ID of the Gmail draft to delete"
                    }
                },
                "required": ["draft_id", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "draft_id" not in args:
            raise RuntimeError("Missing required argument: draft_id")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        success = gmail_service.delete_draft(draft_id=args["draft_id"])

        if success:
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted draft {args['draft_id']}"
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to delete draft {args['draft_id']}"
                )
            ]

class ReplyEmailToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("reply_gmail_email")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Creates and optionally sends a reply to an existing Gmail email with support for HTML formatting and attachments.
            
            The tool automatically:
            - Sets the correct recipient (original sender)
            - Maintains the email thread
            - Adds 'Re:' to the subject if not present
            - Quotes the original message
            
            You can choose to either:
            - Save the reply as a draft (send=false, default)
            - Send the reply immediately (send=true)
            
            The tool supports HTML formatting and file attachments just like create_gmail_draft.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "original_email_id": {
                        "type": "string",
                        "description": "The ID of the Gmail message to reply to"
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text body content of the reply (original message will be quoted below)"
                    },
                    "send": {
                        "type": "boolean",
                        "description": "If true, sends the reply immediately. If false, saves as draft.",
                        "default": False
                    },
                    "cc": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of email addresses to CC"
                    },
                    "html_body": {
                        "type": "string",
                        "description": "Optional HTML version of the reply body. The original message will be quoted in a blockquote below."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of file paths to attach to the reply."
                    }
                },
                "required": ["original_email_id", "body", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["original_email_id", "body"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        
        # First, get the original email
        original_email = gmail_service.get_email_by_id(email_id=args["original_email_id"])
        if original_email is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to retrieve original email with ID: {args['original_email_id']}"
                )
            ]

        # Create the reply
        result = gmail_service.create_reply(
            original_message=original_email,
            reply_body=args["body"],
            send=args.get("send", False),
            cc=args.get("cc"),
            html_body=args.get("html_body"),
            attachments=args.get("attachments")
        )

        if result is None:
            action = "send" if args.get("send", False) else "create"
            return [
                TextContent(
                    type="text",
                    text=f"Failed to {action} reply"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class GetAttachmentToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_gmail_attachment")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Downloads a Gmail attachment to a specified location on the local filesystem.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the Gmail message containing the attachment"
                    },
                    "part_id": {
                        "type": "string",
                        "description": "The part ID of the attachment (obtained from get_gmail_email)"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "The full path where the attachment should be saved (e.g., /tmp/document.pdf)"
                    }
                },
                "required": ["message_id", "part_id", "save_path", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["message_id", "part_id", "save_path"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        message, attachments = gmail_service.get_email_by_id_with_attachments(args["message_id"])
        if message is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to retrieve message with ID: {args['message_id']}"
                )
            ]
        # get attachment_id from part_id
        attachment_id = attachments[args["part_id"]]["attachmentId"]
        attachment_data = gmail_service.get_attachment(args["message_id"], attachment_id)
        if attachment_data is None:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to retrieve attachment with ID: {attachment_id}"
                )
            ]

        file_data = attachment_data["data"]
        # Google's base64 encoding uses - and _ instead of + and /
        try:
            decoded_data = decode_base64_data(file_data)
            with open(args["save_path"], "wb") as f:
                f.write(decoded_data)
            return [
                TextContent(
                    type="text",
                    text=f"Attachment saved to: {args['save_path']}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to save attachment: {str(e)}"
                )
            ]

class BulkSaveAttachmentsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("bulk_save_gmail_attachments")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Downloads multiple Gmail attachments from one or more messages to specified locations.",
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "message_id": {
                                    "type": "string",
                                    "description": "The ID of the Gmail message containing the attachment"
                                },
                                "part_id": {
                                    "type": "string",
                                    "description": "The part ID of the attachment"
                                },
                                "save_path": {
                                    "type": "string",
                                    "description": "The full path where this attachment should be saved"
                                }
                            },
                            "required": ["message_id", "part_id", "save_path"]
                        },
                        "description": "Array of attachment specifications to download",
                        "minItems": 1
                    }
                },
                "required": ["attachments", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "attachments" not in args:
            raise RuntimeError("Missing required argument: attachments")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        gmail_service = gmail.GmailService(user_id=user_id)
        results = []

        for attachment_info in args["attachments"]:
            message, attachments = gmail_service.get_email_by_id_with_attachments(
                attachment_info["message_id"]
            )
            if message is None:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Failed to retrieve message with ID: {attachment_info['message_id']}"
                    )
                )
                continue
            # get attachment_id from part_id
            attachment_id = attachments[attachment_info["part_id"]]["attachmentId"]
            attachment_data = gmail_service.get_attachment(
                attachment_info["message_id"], 
                attachment_id
            )
            if attachment_data is None:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Failed to retrieve attachment with ID: {attachment_id} from message: {attachment_info['message_id']}"
                    )
                )
                continue

            file_data = attachment_data["data"]
            try:    
                decoded_data = decode_base64_data(file_data)
                with open(attachment_info["save_path"], "wb") as f:
                    f.write(decoded_data)
                results.append(
                    TextContent(
                        type="text",
                        text=f"Attachment saved to: {attachment_info['save_path']}"
                    )
                )
            except Exception as e:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Failed to save attachment to {attachment_info['save_path']}: {str(e)}"
                    )
                )
                continue

        return results

class SendEmailToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("send_gmail_email")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Sends an email message immediately via Gmail with support for plain text, HTML formatting, and file attachments.
            
            The tool supports:
            - Plain text emails (body parameter only)
            - HTML formatted emails (both body and html_body parameters)
            - File attachments (list of file paths)
            - CC recipients
            
            This tool sends the email immediately. If you want to create a draft instead, use the create_gmail_draft tool.
            For replies to existing emails, use the reply_gmail_email tool with send=True.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "to": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject line of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text body content of the email"
                    },
                    "cc": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of email addresses to CC"
                    },
                    "html_body": {
                        "type": "string",
                        "description": "Optional HTML version of the email body. If provided, the email will be sent as multipart/alternative with both plain text and HTML versions."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Optional list of file paths to attach to the email. Each path should be an absolute path to a file on the local filesystem."
                    }
                },
                "required": ["to", "subject", "body", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["to", "subject", "body"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
        gmail_service = gmail.GmailService(user_id=user_id)
        result = gmail_service.send_email(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
            cc=args.get("cc"),
            html_body=args.get("html_body"),
            attachments=args.get("attachments")
        )

        if result is None:
            return [
                TextContent(
                    type="text",
                    text="Failed to send email"
                )
            ]

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

class ListLabelsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("list_gmail_labels")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""List all available Gmail labels for the user's account.
            
            Returns both system labels (like INBOX, SENT, TRASH) and custom labels.
            Each label includes its ID (needed for other operations), name, type, and visibility settings.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema()
                },
                "required": [toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
            
        gmail_service = gmail.GmailService(user_id=user_id)
        labels = gmail_service.list_labels()
        
        return [
            TextContent(
                type="text",
                text=json.dumps(labels, indent=2)
            )
        ]

class ModifyLabelsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("modify_gmail_labels")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Add or remove labels from Gmail messages.
            
            Common operations:
            - Archive: Remove 'INBOX' label
            - Mark as read: Remove 'UNREAD' label
            - Mark as unread: Add 'UNREAD' label
            - Star: Add 'STARRED' label
            - Mark as important: Add 'IMPORTANT' label
            - Move to trash: Add 'TRASH' label (prefer using trash_gmail_messages tool)
            - Apply custom labels: Use label IDs from list_gmail_labels
            
            Note: System label IDs like 'INBOX', 'UNREAD', 'STARRED' can be used directly.
            For custom labels, use the label ID (not the name) obtained from list_gmail_labels.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "message_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of message IDs to modify. Can be a single ID or multiple IDs for batch operations.",
                        "minItems": 1
                    },
                    "add_labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Label IDs to add (e.g., 'IMPORTANT', 'STARRED', 'UNREAD', or custom label IDs)"
                    },
                    "remove_labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Label IDs to remove (e.g., 'INBOX' to archive, 'UNREAD' to mark as read)"
                    }
                },
                "required": ["message_ids", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "message_ids" not in args:
            raise RuntimeError("Missing required argument: message_ids")
            
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
            
        gmail_service = gmail.GmailService(user_id=user_id)
        message_ids = args["message_ids"]
        add_labels = args.get("add_labels", [])
        remove_labels = args.get("remove_labels", [])
        
        # Check if we have any labels to modify
        if not add_labels and not remove_labels:
            return [
                TextContent(
                    type="text",
                    text="No labels specified to add or remove"
                )
            ]
        
        # Batch operation for multiple messages
        if len(message_ids) > 1:
            success = gmail_service.batch_modify_messages(
                message_ids=message_ids,
                add_labels=add_labels,
                remove_labels=remove_labels
            )
            
            if success:
                return [
                    TextContent(
                        type="text",
                        text=f"Successfully modified labels for {len(message_ids)} messages"
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text="Failed to modify labels for messages"
                    )
                ]
        
        # Single message operation
        else:
            result = gmail_service.modify_message_labels(
                message_id=message_ids[0],
                add_labels=add_labels,
                remove_labels=remove_labels
            )
            
            if result:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text="Failed to modify labels for message"
                    )
                ]

class TrashMessagesToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("trash_gmail_messages")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Move Gmail messages to trash.
            
            This tool uses the dedicated trash API for better reliability than adding the TRASH label.
            Messages in trash are automatically deleted after 30 days.
            To restore messages from trash, use modify_gmail_labels to remove the TRASH label.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "message_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of message IDs to move to trash. Can be a single ID or multiple IDs.",
                        "minItems": 1
                    }
                },
                "required": ["message_ids", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "message_ids" not in args:
            raise RuntimeError("Missing required argument: message_ids")
            
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
            
        gmail_service = gmail.GmailService(user_id=user_id)
        message_ids = args["message_ids"]
        
        results = []
        
        # Batch operation for multiple messages
        if len(message_ids) > 1:
            success = gmail_service.batch_trash_messages(message_ids)
            if success:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Successfully moved {len(message_ids)} messages to trash"
                    )
                )
            else:
                results.append(
                    TextContent(
                        type="text",
                        text="Failed to move messages to trash"
                    )
                )
        else:
            # Single message operation
            result = gmail_service.trash_message(message_ids[0])
            if result:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Successfully moved message {message_ids[0]} to trash"
                    )
                )
            else:
                results.append(
                    TextContent(
                        type="text",
                        text=f"Failed to move message {message_ids[0]} to trash"
                    )
                )
        
        return results

class CreateLabelToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_gmail_label")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Create a new custom Gmail label.
            
            Labels help organize emails and can be applied to messages using modify_gmail_labels.
            Once created, the label will appear in the label list with a unique ID.
            """,
            inputSchema={
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "name": {
                        "type": "string",
                        "description": "The display name for the label"
                    },
                    "label_list_visibility": {
                        "type": "string",
                        "enum": ["labelShow", "labelShowIfUnread", "labelHide"],
                        "description": "Visibility of the label in the label list (default: labelShow)",
                        "default": "labelShow"
                    },
                    "message_list_visibility": {
                        "type": "string",
                        "enum": ["show", "hide"],
                        "description": "Visibility of the label in the message list (default: show)",
                        "default": "show"
                    }
                },
                "required": ["name", toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "name" not in args:
            raise RuntimeError("Missing required argument: name")
            
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
            
        gmail_service = gmail.GmailService(user_id=user_id)
        
        result = gmail_service.create_label(
            name=args["name"],
            label_list_visibility=args.get("label_list_visibility", "labelShow"),
            message_list_visibility=args.get("message_list_visibility", "show")
        )
        
        if result:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Failed to create label '{args['name']}'"
                )
            ]