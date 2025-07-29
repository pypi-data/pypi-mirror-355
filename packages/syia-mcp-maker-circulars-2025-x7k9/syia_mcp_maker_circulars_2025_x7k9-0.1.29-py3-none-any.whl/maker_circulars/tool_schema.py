from maker_circulars.databases import * 
import mcp.types as types
from typing import List, Dict, Any, Union
from enum import Enum 
from logging import Logger
import json
import datetime

# Typesense tool definitions for circulars

typesense_tools = [ 
            # Circular Tools
            types.Tool(
                name = "smart_circular_search",
                description = (
                    "Universal search tool for circulars from equipment makers. "
                    "This is the primary tool for querying technical or procedural circulars. "
                    "It intelligently adapts search strategy based on query intent and can handle "
                    "everything from specific lookups to general browsing."
                ),
                inputSchema = {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural language query to search circulars. Leave blank to browse. "
                                "Examples: 'oil mist detector retrofit', 'MD-SX controller installation instructions', "
                                "'replacement parts for MD-14M'"
                            )
                        },
                        "search_type": {
                            "type": "string",
                            "description": "Search strategy. Fixed to 'semantic' for conceptual queries.",
                            "enum": ["semantic"],
                            "default": "semantic"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters to narrow down results",
                            "properties": {
                                "maker": {
                                    "type": "string",
                                    "description": "Maker or company issuing the circular"
                                },
                                "document_name": {
                                    "type": "string",
                                    "description": "Exact document name (case-insensitive)"
                                },
                                "from_date": {
                                    "type": "string",
                                    "description": "Only include circulars from this date onwards in a dd/mm/yyyy format"
                                },
                                "to_date": {
                                    "type": "string",
                                    "description": "Only include circulars up to this date in a dd/mm/yyyy format"
                                }
                            }
                        },
                        "max_results": {
                            "type": "number",
                            "description": "Number of results to return",
                            "default": 7,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_maker_specific_circulars",
                description="Retrieves all technical circulars issued by a specific equipment manufacturer (e.g., 'MAN B&W', 'Wärtsilä'). Technical circulars contain critical updates about equipment modifications, safety alerts, and performance improvements. Use this tool to get a comprehensive list of all circulars from a particular manufacturer, sorted by date with the most recent first.",
                inputSchema={
                    "type": "object",
                    "required": ["maker"],
                    "properties": {
                        "maker": {
                            "type": "string",
                            "description": "Name of the equipment maker. Example: 'MAN B&W'."
                        }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_circular_by_doc_name_or_num",
                description="Locates specific technical circulars using any part of the document name or reference number. For example, searching for 'USI-40048' or 'Turbocharger Design change' will find matching circulars. This tool is helpful when you know a portion of the circular's title or reference number and need to retrieve the full document.",
                inputSchema={
                    "type": "object",
                    "required": ["document_name_or_num"],
                    "properties": {
                        "document_name_or_num": {
                            "type": "string",
                            "description": "A text snippet containing part of the document name or number. Example: 'USI-40048-ERev.1_MET type Turbocharger Design change of MET Turbocharger locking washer'."
                        }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_circular_by_maker_and_date_range",
                description="Retrieves technical circulars from a specific manufacturer within a defined date period, with a maximum range of 1 year. If the requested date range exceeds 1 year, returns only the most recent year's data within that range and provides information about the remaining period. For example, if requesting 2022-01-01 to 2024-12-31, it will return data from 2023-12-31 to 2024-12-31 with guidance on querying the earlier period. Specify the equipment maker (e.g., 'MAN B&W') along with start and end dates to locate all relevant technical updates from that timeframe. Useful for reviewing all technical advisories issued during a specific period.",
                inputSchema={
                    "type": "object",
                    "required": ["maker"],
                    "properties": {
                        "maker": {
                            "type": "string",
                            "description": "Name of the equipment maker. Example: 'MAN B&W', 'Wärtsilä'."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format. If not provided, defaults to 1 year before end_date or current date. Example: '2023-10-28'"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format. If not provided, defaults to current date. Example: '2024-10-28'. Note: Maximum range between start_date and end_date is 1 year."
                        }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="fetch_circular_details_by_vector_search",
                description="Performs a flexible search across all technical circulars using multiple criteria. You can search by manufacturer, document name/content. This comprehensive search tool helps locate relevant technical circulars when you're not sure about exact details or need to find all circulars matching certain parameters.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query by the user to search for a circular. Example: 'Engine Maintenance Update 2025-01'."
                        }
                        # "document_name": {
                        #     "type": "string",
                        #     "description": "The name of the circular or document. Example: 'Engine Maintenance Update 2025-01'."
                        # },
                        # "start_date": {
                        #     "type": "string",
                        #     "description": "Start date in YYYY-MM-DD format. Example: '2023-10-28'."
                        # },
                        # "end_date": {
                        #     "type": "string",
                        #     "description": "End date in YYYY-MM-DD format. Example: '2025-04-29'."
                        # }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_all_circular_makers",
                description="Provides a complete list of equipment manufacturers who have issued technical circulars in the system. Use this tool to see which manufacturers' circulars are available and to confirm the exact spelling of manufacturer names for further searches. Helpful when you need to research updates for a specific brand of equipment.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            )
        ]

# MongoDB tool definitions for circulars

mongodb_tools = [
    types.Tool(
    name="get_maker_model_for_particular_imo",
    description=(
        "Query MongoDB for a given imo and return machinery details "
        "filtered to components 'Aux Engine' or 'Main Engine'"
        "Return the data including vesselName, makerName, model, and component."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "imo": {
                "type": "string", 
                "description": "The imo of the vessel to query."
            }
        },  
        "required": ["imo"]
    },
    returns="list[dict]"
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

shippalm_tools = [
    types.Tool(
        name="latest_circulars_manbw_downloads",
        description="Download service letters from MAN B&W website and return download information",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        },
        returns="list[dict]"
    ),
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
#                     "examples": [["example@syia.com"]]
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

tool_definitions = typesense_tools + mongodb_tools + shippalm_tools + general_tools 