from mcp_communication.databases import * 
import mcp.types as types
from typing import List, Dict, Any, Union
from enum import Enum 
from logging import Logger
import json
import datetime

# Communication Tools

communication_tools = [
    types.Tool(
        name="mail_communication",
        description=(
            "Use this tool to send formal emails to one or more recipients. "
            "It supports a subject line, an HTML-formatted email body, and optional CC and BCC fields. "
            "Use this tool when you have email addresses of the people you want to contact. You can send the same message to many people at once.."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": (
                        "The subject line of the email. Keep it concise and professional. "
                        "Maximum length is 100 characters."
                    ),
                    "maxLength": 100
                },
                "content": {
                    "type": "string",
                    "description": (
                        "The main content of the email, written in HTML. "
                        "This allows formatting like bold text, lists, and links. "
                        "End the message with the signature: 'Best regards,<br>Syia'."
                    )
                },
                "recipient": {
                    "type": "array",
                    "description": (
                        "A list of email addresses for the main recipients (To field). "
                        "Must contain at least one valid email address."
                    ),
                    "items": {"type": "string", "format": "email"},
                    "examples": [["example@syia.com"]]
                },
                "cc": {
                    "type": "array",
                    "description": (
                        "Optional list of email addresses to be included in the CC (carbon copy) field."
                    ),
                    "items": {"type": "string", "format": "email"}
                },
                "bcc": {
                    "type": "array",
                    "description": (
                        "Optional list of email addresses to be included in the BCC (blind carbon copy) field."
                    ),
                    "items": {"type": "string", "format": "email"}
                }
            },
            "required": ["subject", "content", "recipient"]
        }
    ),
    types.Tool(
        name="whatsapp_communication",
        description=(
            "Use this tool to send quick, informal text messages via WhatsApp. "
            "It is designed for real-time, individual communication using a phone number. "
            "Only one phone number can be messaged per tool call."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": (
                        "The message to send. Must be plain text. "
                        "Keep the message short and to the point."
                    )
                },
                "recipient": {
                    "type": "string",
                    "description": (
                        "The recipient's WhatsApp phone number. "
                        "It can be in international E.164 format (e.g., +14155552671) or a local number (e.g., 9876543210), "
                        "which will be automatically normalized."
                    ),
                    "pattern": "^(\+?[1-9]\\d{1,14}|\\d{6,15})$",
                    "examples": ["+919876543210", "9876543210"]
                }
            },
            "required": ["content", "recipient"]
        }
    )
]

 
# Combined tools for compatibility

tool_definitions = communication_tools