from mcp_communication.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional 
from pydantic import BaseModel
import mcp.types as types
from mcp_communication import mcp, logger
import requests
from mcp_communication.tool_schema import tool_definitions
import datetime
from typing import Any, Dict, List, Union, Sequence
import cohere
from mcp_communication.constants import COHERE_API_KEY
from playwright.async_api import async_playwright
from pathlib import Path
from mcp_communication.utils import timestamped_filename, timestamped_filename_pdf
from pymongo import MongoClient, errors
import os
import re

from utils.llm import LLMClient
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from dateutil import parser
import time
import difflib
import requests 
from typing import Dict, Any, List, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import base64
from typing import List, Optional
import re
import requests
from typing import Dict, Any
from .constants import MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY, PERPLEXITY_API_KEY, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_AUTH_URI, OAUTH_TOKEN_URI, OAUTH_REDIRECT_URIS, OAUTH_SCOPES, WHATSAPP_TOKEN, WHATSAPP_URL

import httpx

import re
import base64
import pickle
from typing import List, Optional, Dict, Any, Union
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 

from pydantic import EmailStr

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

import os
import requests
import logging

server_tools = tool_definitions

def register_tools():
    """Register all tools with the MCP server."""
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List all available tools."""
        logger.info("Listing available tools")
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None 
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        """Call a specific tool by name with the given arguments."""
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        try:
            if name == "mail_communication":
                return await mail_communication(arguments)
            elif name == "whatsapp_communication":
                return await whatsapp_communication(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")
        

async def mail_communication(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:

    # def comma_split_emails(s: str) -> List[EmailStr]:
    #     return [str(e.strip()) for e in s.split(",") if e.strip()]
    
    final_input = {
        'subject': arguments.get("subject"),
        'content': arguments.get("content"),
        'recipient': arguments.get("recipient"),
        'cc': arguments.get("cc", None),
        'bcc': arguments.get('bcc', None)
    }

    def g_authenticate_with_keys(
        scopes: list,
        api_name: str,
        api_version: str,
        token_path: str
    ):
        """
        Authenticate and return a Google API service client.

        Args:
            client_id: Google OAuth2 client ID.
            client_secret: Google OAuth2 client secret.
            scopes: List of scopes required (e.g., Gmail, Sheets).
            api_name: API name to access (default is 'sheets').
            api_version: API version (default is 'v4').
            token_path: Where to save or load token (default: 'oauth_token.pickle').

        Returns:
            A resource object for the specified Google API.
        """
        creds = None

        # Load token if it exists
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token_file:
                creds = pickle.load(token_file)

        # If no valid creds, refresh or authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": OAUTH_CLIENT_ID,
                            "client_secret": OAUTH_CLIENT_SECRET,
                            "auth_uri": OAUTH_AUTH_URI,
                            "token_uri": OAUTH_TOKEN_URI,
                            "redirect_uris": [OAUTH_REDIRECT_URIS]
                        }
                    },
                    scopes
                )
                creds = flow.run_local_server(port=0)
                with open(token_path, 'wb') as token_file:
                    pickle.dump(creds, token_file)

        return build(api_name, api_version, credentials=creds)
    
    GMAIL_SCOPES = [OAUTH_SCOPES]

    def send_gmail(
        subject: str,
        content: str,
        recipient: List[EmailStr],
        cc: Optional[List[EmailStr]] = None,
        bcc: Optional[List[EmailStr]] = None
    ):
        try:
            # Authenticate and get Gmail service
            service = g_authenticate_with_keys(scopes = GMAIL_SCOPES, api_name='gmail', api_version='v1', token_path = "mcp_gmail_token.pickle")

            message = MIMEMultipart()
            message["from"] = "me"
            message["to"] = ", ".join(recipient)
            message["subject"] = subject
            if cc:
                message["Cc"] = ", ".join(cc)
            if bcc:
                message["Bcc"] = ", ".join(bcc)

            message.attach(MIMEText(content, "html"))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            sent_message = service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()

            return {
                "status":"success",
                "output":f"Email sent! ID: {sent_message['id']}"
            }

        except Exception as e:
            return {
                "status":"failure",
                "output":f"Failed to send email: {e}"
            }

    try:
        maildata = send_gmail(**final_input)

        return [
            types.TextContent(
                type="text", 
                text=f"{maildata}"
            )
        ]

    except Exception as e:
        logger.error(f"Failure to communicate through mail: {e}")
        raise



async def whatsapp_communication(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:

    input = {
        'content': arguments.get("content"),
        'recipient': arguments.get("recipient")
    }

    def sanitize_whatsapp_text(text: str) -> str:
        # Strip HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Replace multiple spaces with one
        clean = re.sub(r'\s{2,}', ' ', clean)
        # Replace newlines/tabs with space
        clean = clean.replace('\n', ' ').replace('\t', ' ')
        return clean.strip()

    def send_whatsapp(
        content: str,
        recipient: str
    ):
        try:
            url = WHATSAPP_URL

            headers = {
                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                "Content-Type": "application/json"
            }

            body = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "template",
                    "template": {
                        "name": "whatsapp_template",
                        "language": {
                        "code": "en"
                        },
                        "components": [
                        {
                            "type": "body",
                            "parameters": [
                            {
                                "type": "text",
                                "text":content
                            }
                            ]
                        }
                        ]
                    }
                    }

            response = requests.post(url, headers=headers, json=body)

            if response.status_code == 200:
                return {
                    "status":"success",
                    "output":f"Message sent to {recipient}"
                }
            else:
                return {
                    "status":"failure",
                    "output":f"Error {response.status_code}: {response.text}"
                }

        except Exception as e:
            return {
                "status":"failure",
                "output":f"Exception: {str(e)}"
            }

    try:
        input['content'] = sanitize_whatsapp_text(input['content'])
        result = send_whatsapp(**input)

        if result["status"] == "success":
            return [
                types.TextContent(
                    type="text",
                    text=f"Whatsapp message sent successfully: {result['output']}"
                )
            ]
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Whatsapp message failed: {result['output']}"
                )
            ]

    except Exception as e:
        logger.error(f"Failure to communicate through whatsapp: {e}")
        raise
