from imo_publications.databases import *    
import mcp.types as types
from typing import List, Dict, Any, Union
from enum import Enum
from logging import Logger
import json
import datetime

# Typesense tool definitions for IMO publications

typesense_tools = [
            # IMO Publication Tools
            types.Tool(
                name="list_imo_publications",
                description="Provides a complete catalog of all available International Maritime Organization (IMO) publications in the system, including critical regulations like SOLAS, MARPOL, and STCW. Use this tool to see which official IMO regulatory documents, codes, and guidelines are available for reference. Essential for identifying applicable maritime regulations and compliance requirements.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="fetch_imo_publication_by_vector_search",
                description="Performs comprehensive search across all IMO regulatory publications based on document name or content. Use this tool to find specific regulations, requirements, or guidelines within IMO conventions, codes, and circulars. Simply enter relevant keywords (e.g., 'fire safety', 'ballast water', 'hours of rest') to locate applicable regulatory text across all IMO publications. Vital for regulatory compliance verification and interpretation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_name": {
                            "type": "string",
                            "description": "Optional full or partial name of the IMO publication to search for. Example: 'SOLAS', 'MARPOL', 'GMDSS'."
                        }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_by_imo_publication_name",
                description="Locates specific IMO publications using any part of the document name or reference number. This tool is helpful when you know a portion of the publication's title or reference number and need to retrieve the full document.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_name": {
                            "type": "string",
                            "description": "A text snippet containing part of the IMO publication name or number. Example: 'SOLAS', 'MARPOL', 'GMDSS'."
                        }
                    },
                    "required": ["document_name"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="smart_imo_publication_search",
                description=(
                    "Universal search tool for IMO publications. "
                    "This is the primary tool for finding any information in the IMO publication database. "
                    "It intelligently adapts search strategy based on query intent and can handle "
                    "everything from specific lookups to general browsing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural language search query. Leave empty for browsing mode. "
                                "Examples: 'SOLAS fire safety', 'MARPOL Annex VI', 'GMDSS requirements', 'chapter II-2'"
                            ),
                        },
                        "search_type": {
                            "type": "string",
                            "description":  "Search strategy. Fixed to 'semantic' for conceptual queries.",
                            "enum":  ["semantic"],
                            "default": "semantic"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filters to narrow search results. All filters are optional and use exact matching",
                            "properties": {
                                "document_name": {
                                    "type": "string",
                                    "description": "Exact or partial name of the IMO publication",
                                },
                                "chapter": {
                                    "type": "string",
                                    "description": "Chapter name or number to search within",
                                },
                                "section": {
                                    "type": "string",
                                    "description": "Section name to search within",
                                },
                                "page_range": {
                                    "type": "array",
                                    "items": {
                                        "type": "number"
                                    },
                                    "minItems": 2,
                                    "maxItems": 2,
                                    "description": "Page range to search within [start_page, end_page]"
                                },
                                # Remove the 'year' property from filters
                                # "year": {
                                #     "type": "integer",
                                #     "description": "Year of document revision",
                                #     "minimum": 1930,
                                #     "maximum": 2030
                                # }
                            }
                        },
                        "max_results": {
                            "type": "number",
                            "description": "Maximum number of results to return",
                            "default": 7,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            )
        ]

# MongoDB tool definitions

mongodb_tools = [
    types.Tool(
        name="get_table_schema",
        description="This tool retrieves Typesense schema and instructions on how to query a typesense table for a specific category.",
        inputSchema={
            "type": "object",
            "required": ["category"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category for which to retrieve the Typesense schema (e.g., circulars, notices, announcements).",
                    "enum": ["imo_publication"]
                }
            }            
        }
    ),
    # types.Tool( 
    #     name="create_update_casefile",
    #     description="Creates a structured mongoDB entry associated with a specific vessel identified by its IMO number and casefile.",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "integer",
    #                 "description": "IMO number uniquely identifying the vessel. Required for correctly associating the case file with the corresponding ship in the database."
    #             },
    #             "content": {
    #                 "type": "string",
    #                 "description": "The full body or detailed narrative of the case file. This may include observations, incident logs, root cause analysis, technical notes, or investigation findings related to the vessel."
    #             },
    #             "casefile": {
    #                 "type": "string",
    #                 "description": "A short and concise summary or title for the case file, such as 'Main Engine Overheating - April 2025' or 'Hull Inspection Report'. This should briefly describe the nature or subject of the entry."
    #             }
    #         },
    #         "required": ["imo", "content", "casefile"]
    #     }
    # )
]

# Document Parser Tools
general_tools = [
    types.Tool(
        name="google_search",
        description="Perform a Google search using a natural language query. Returns relevant web results.",
        inputSchema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to be executed."
                }
            },
          "additionalProperties": False
        }
    )
]
          
document_parser_tools = [
    types.Tool(
        name="parse_document_link",
        description="Use this tool to parse a document link or a local file. The tool will parse the document and return the text content.",
        inputSchema={
            "type": "object",
            "required": ["document_link"],
            "properties": {
                "document_link": {
                    "type": "string",
                    "description": "The link to the document that needs to be parsed"
                }
            },
            "additionalProperties": False
        }
    )
]

# Communication Tools

# communication_tools = [
#     types.Tool(
#         name="mail_communication",
#         description=(
#             "Use this tool to send formal emails to one or more recipients. "
#             "It supports a subject line, an HTML-formatted email body, and optional CC and BCC fields. "
#             "Use this tool when you have email addresses of the people you want to contact. You can send the same message to many people at once.."
#         ),
#         inputSchema={
#             "type": "object",
#             "properties": {
#                 "subject": {
#                     "type": "string",
#                     "description": (
#                         "The subject line of the email. Keep it concise and professional. "
#                         "Maximum length is 100 characters."
#                     ),
#                     "maxLength": 100
#                 },
#                 "content": {
#                     "type": "string",
#                     "description": (
#                         "The main content of the email, written in HTML. "
#                         "This allows formatting like bold text, lists, and links. "
#                         "End the message with the signature: 'Best regards,<br>Syia'."
#                     )
#                 },
#                 "recipient": {
#                     "type": "array",
#                     "description": (
#                         "A list of email addresses for the main recipients (To field). "
#                         "Must contain at least one valid email address."
#                     ),
#                     "items": {"type": "string", "format": "email"},
#                     "examples": [["example@domain.com"]]
#                 },
#                 "cc": {
#                     "type": "array",
#                     "description": (
#                         "Optional list of email addresses to be included in the CC (carbon copy) field."
#                     ),
#                     "items": {"type": "string", "format": "email"}
#                 },
#                 "bcc": {
#                     "type": "array",
#                     "description": (
#                         "Optional list of email addresses to be included in the BCC (blind carbon copy) field."
#                     ),
#                     "items": {"type": "string", "format": "email"}
#                 }
#             },
#             "required": ["subject", "content", "recipient"]
#         }
#     ),
#     types.Tool(
#         name="whatsapp_communication",
#         description=(
#             "Use this tool to send quick, informal text messages via WhatsApp. "
#             "It is designed for real-time, individual communication using a phone number. "
#             "Only one phone number can be messaged per tool call."
#         ),
#         inputSchema={
#             "type": "object",
#             "properties": {
#                 "content": {
#                     "type": "string",
#                     "description": (
#                         "The message to send. Must be plain text. "
#                         "Keep the message short and to the point."
#                     )
#                 },
#                 "recipient": {
#                     "type": "string",
#                     "description": (
#                         "The recipient's WhatsApp phone number. "
#                         "It can be in international E.164 format (e.g., +14155552671) or a local number (e.g., 9876543210), "
#                         "which will be automatically normalized."
#                     ),
#                     "pattern": "^(\+?[1-9]\\d{1,14}|\\d{6,15})$",
#                     "examples": ["+919876543210", "9876543210"]
#                 }
#             },
#             "required": ["content", "recipient"]
#         }
#     )
# ]


# Combined tools for compatibility
tool_definitions = typesense_tools + mongodb_tools + document_parser_tools + general_tools
