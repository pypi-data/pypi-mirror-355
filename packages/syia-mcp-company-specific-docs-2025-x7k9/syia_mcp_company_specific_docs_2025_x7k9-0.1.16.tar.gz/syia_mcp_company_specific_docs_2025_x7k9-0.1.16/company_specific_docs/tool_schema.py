from company_specific_docs.databases import * 
import mcp.types as types
from typing import List, Dict, Any, Union 
from enum import Enum
from logging import Logger
import json
import datetime 

company_manual_browse_tools = [
 
    # 1. List available manuals
    types.Tool(
        name="list_company_manuals",
        description="Returns a list of all available company manuals by name. Use this to discover which company manuals exist.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),

    # types.Tool(
    #     name="smart_company_manual_search",
    #     description=(
    #         "Universal search tool for company manuals, risk assessments, forms and checklists, and manager's instructions. "
    #         "This is the primary tool for finding any information in the company manual database. "
    #         "It intelligently adapts search strategy based on query intent and can handle "
    #         "everything from specific lookups to general browsing."
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "query": {
    #                 "type": "string",
    #                 "description": (
    #                     "Natural language search query. Leave empty for browsing mode. "
    #                     "Examples: 'safety management system', 'incident reporting procedure', "
    #                     "'risk assessment for hot work', 'manager instruction on overtime'"
    #                 ),
    #             },
    #             "search_type": {
    #                 "type": "string",
    #                 "description": (
    #                     "Search strategy. Use 'semantic' for conceptual queries, 'keyword' for exact terms/document numbers, "
    #                     "'hybrid' for best of both (default), 'browse' for exploring without query"
    #                 ),
    #                 "enum": ["semantic", "keyword", "hybrid", "browse"],
    #                 "default": "hybrid"
    #             },
    #             "filters": {
    #                 "type": "object",
    #                 "description": "Filters to narrow search results. All filters are optional and use exact matching",
    #                 "properties": {
    #                     "document_name": {
    #                         "type": "string",
    #                         "description": "Exact or partial name of the manual document",
    #                     },
    #                     "document_type": {
    #                         "type": "string",
    #                         "description": "Category of document",
    #                         "enum": ["company manual", "risk assessment", "forms and checklists", "manager instruction"]
    #                     },
    #                     "chapter": {
    #                         "type": "string",
    #                         "description": "Chapter name or number to search within",
    #                     },
    #                     "section": {
    #                         "type": "string",
    #                         "description": "Section name to search within",
    #                     },
    #                     "page_range": {
    #                         "type": "array",
    #                         "items": {
    #                             "type": "number"
    #                         },
    #                         "minItems": 2,
    #                         "maxItems": 2,
    #                         "description": "Page range to search within [start_page, end_page]"
    #                         # "examples": [[10, 25], [100, 150]]
    #                     },
    #                     "year": {
    #                         "type": "number",

    #                         "description": "Year of document revision",
    #                         "minimum": 1930,
    #                         "maximum": 2030
    #                     }
    #                 }
    #             },
    #             "max_results": {
    #                 "type": "number",
    #                 "description": "Maximum number of results to return",
    #                 "default": 20,
    #                 "minimum": 1,
    #                 "maximum": 100  
    #             }
    #         },
    #         "required": [],
    #         "additionalProperties": False
    #     }
    # ),
    
    types.Tool(
        name="smart_company_manual_search",
        description=(
            "Universal search tool for company manuals, risk assessments, forms and checklists, and manager's instructions. "
            "This is the primary tool for finding any information in the company manual database. "
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
                        "Examples: 'safety management system', 'incident reporting procedure', "
                        "'risk assessment for hot work', 'manager instruction on overtime'"
                    ),
                },
                "search_type": {
                    "type": "string",
                    "description": "Search strategy. Fixed to 'semantic' for conceptual queries.",
                    "enum": ["semantic"],
                    "default": "semantic"
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to narrow search results. All filters are optional and use exact matching",
                    "properties": {
                        "document_name": {
                            "type": "string",
                            "description": "Exact or partial name of the manual document",
                        },
                        "document_type": {
                            "type": "string",
                            "description": "Category of document",
                            "enum": ["company manual", "risk assessment", "forms and checklists", "manager instruction"]
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
                        "year": {
                            "type": "number",
                            "description": "Year of document revision",
                            "minimum": 1930,
                            "maximum": 2030
                        }
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
    ),


    types.Tool(
        name="fetch_company_documents_by_vector_search",
        description="Performs a targeted search across company policy manuals, risk assessments, forms and checklists, and management directives. Use this tool to locate specific policies, procedures, risk control measures, or official leadership instructions by entering relevant keywords such as document names, activity types, hazards, departments, or operational requirements.",
        inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query by the user to search for a company policy, risk assessment, or management directive. Example: 'Engine Maintenance Update 2025-01'."
                        }
            },
            "additionalProperties": False
        }
    ),
 
    types.Tool( 
        name="get_by_company_document_name_or_num",
        description="Locates specific manuals, risk assesment, forms and checklists, and manager's instructions using any part of the document name or reference number. This tool is helpful when you know a portion of the manual's title or reference number and need to retrieve the full document.",
        inputSchema={
            "type": "object",
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "A text snippet containing part of the document name or number. Example: 'Incident', 'Safety'."
                },
                "document_type": {
                    "type": "string",
                    "description": "The type of document to search for.",
                    "enum": ["company manual", "risk assessment", "forms and checklists", "manager instruction"]
                }
            },
            "additionalProperties": False
        } 
    ),

    # 2. Get full TOC: chapters + sections
    types.Tool(
        name="get_company_manual_structure",
        description="Returns the full structure of a company manual, including its chapters and the sections within each chapter.",
        inputSchema={
            "type": "object",
            "required": ["document_name"],
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "The exact name of the company manual (as returned by list_company_manuals)."
                }
            }
        }
    ),
 
    # 3. Get list of sections (and summaries) within a chapter
    types.Tool(
        name="get_company_manual_chapter_overview",
        description="Returns a list of sections within a chapter of a company manual, along with brief descriptions of each section",
        inputSchema={ 
            "type": "object",
            "required": ["document_name", "chapter"],
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Exact name of the company manual."
                },
                "chapter": {
                    "type": "string",
                    "description": "Exact chapter name to get overview for."
                }
            },
            "additionalProperties": False
        }
    ),
 
    # 4. Read the full content of a specific section
    types.Tool(
        name="read_company_manual_section",
        description="Returns the full text content of a specific section from a company manual. Requires the manual name, chapter name, and section name.",
        inputSchema={
            "type": "object",
            "required": ["document_name", "chapter", "section"],
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Exact name of the company manual."
                },
                "chapter": {
                    "type": "string",
                    "description": "Exact chapter name."
                },
                "section": {
                    "type": "string",
                    "description": "Exact section name."
                }
            },
            "additionalProperties": False
        }
    ),
 
    # 5. Read arbitrary page range (for extended context)
    types.Tool(
        name="read_company_manual_by_page_range",
        description="Returns content from a company manual for a given page range. Useful when additional context is needed beyond a section.",
        inputSchema={
            "type": "object",
            "required": ["document_name", "start_page", "end_page"],
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Exact name of the company manual."
                },
                "start_page": {
                    "type": "number",
                    "description": "Start page of the page range."
                },
                "end_page": {
                    "type": "number",
                    "description": "End page of the page range."
                }
            },
            "additionalProperties": False
        }
    )
]

mongodb_tools = [
    types.Tool( 
        name="create_update_casefile",
        description="Creates a structured mongoDB entry associated with a specific vessel identified by its IMO number and casefile.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "number",
                    "description": "IMO number uniquely identifying the vessel. Required for correctly associating the case file with the corresponding ship in the database."
                },
                "content": {
                    "type": "string",
                    "description": "The full body or detailed narrative of the case file. This may include observations, incident logs, root cause analysis, technical notes, or investigation findings related to the vessel."
                },
                "casefile": {
                    "type": "string",
                    "description": "A short and concise summary or title for the case file, such as 'Main Engine Overheating - April 2025' or 'Hull Inspection Report'. This should briefly describe the nature or subject of the entry."
                }
            },
            "required": ["imo", "content", "casefile"]
        }
    )

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
    ),
    types.Tool(
        name="get_mcp_build_version",
        description="Get the current build version of the MCP server.",
        inputSchema={
            "type": "object",
            "properties": {}
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
tool_definitions = company_manual_browse_tools + mongodb_tools + general_tools
