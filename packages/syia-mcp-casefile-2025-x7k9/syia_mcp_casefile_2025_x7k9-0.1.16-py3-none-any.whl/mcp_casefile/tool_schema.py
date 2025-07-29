from .databases import *
import mcp.types as types


 
# MongoDB tool definitions for mcp_purchase

mongodb_tools = [
    types.Tool(
        name = "get_casefile_index",
        description = "Get the casefile index",
        inputSchema = {
            "type": "object",
            "properties": {
                "casefile_id": {
                    "type": "string", 
                    "description": "ID of the casefile"
                    },
                "limit": {
                    "type": "number", 
                    "description": "Max log entries to return.", 
                    "minimum": 1, 
                    "default": 10
                    }, 
                "next_iter": {
                    "type": "number", 
                    "description": "The pagination parameter. If 0, returns the latest entries. If 1, returns the next batch of older entries, and so on.", 
                    "default": 0
                    }
            },
            "required": ["casefile_id"]
        }
    ),
    types.Tool(
        name = "get_casefile_pages",
        description = "Get the casefile pages",
        inputSchema = {
            "type": "object",
            "properties": {
                "casefile_id": {
                    "type": "string", 
                    "description": "ID of the casefile"
                    },
                "pages": {
                    "type": "array",
                    "description": "List of page numbers to fetch should be whole numbers (e.g., [1, 3, 5])",
                    "items": {
                        "type": "number"
                    }
                }
            },
            "required": ["casefile_id", "pages"]
        }
    ),
    types.Tool(
        name = "get_latest_plan",
        description = "Get the latest plan for the casefile",
        inputSchema = {
            "type": "object",
            "properties": {
                "casefile_id": {
                    "type": "string", 
                    "description": "ID of the casefile"
                    }
            },
            "required": ["casefile_id"]
        }
    ),
    types.Tool(
        name = "write_plan",
        description = "Write a plan for the casefile",
        inputSchema = {
            "type": "object",
            "properties": {
                "casefile_id": {
                    "type": "string", 
                    "description": "ID of the casefile"
                    }
            },
            "required": ["casefile_id"]
        }
    ),
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
    ),
        types.Tool(
        name="get_vessel_details",
        description="Retrieves vessel details including IMO number, vessel name,class,flag,DOC and the ERP version for a specific vessel.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Pass the vessel name to search for the IMO number"
                }
            },
            "required": ["query"]
        }
    )
]


# Typesense tool definitions for mcp_purchase

typesense_tools = [
    # types.Tool(
    #     name = "search_casefile",
    #     description = """Search and retrieve casefiles from the database. This function returns the top matching casefiles 
    #     along with their casefile IDs based on the search query.
    #     
    #     IMPORTANT: When a vessel name is mentioned in the user query or context:
    #     1. MUST first use the get_vessel_details tool to obtain the IMO number
    #     2. MUST pass the retrieved IMO number to the 'imo' parameter
    #     3. This ensures only casefiles for the correct vessel are returned
    #     
    #     The tool can filter results by vessel when IMO is provided""",
    #     inputSchema = {
    #         "type": "object",
    #         "properties": {
    #             "query": {
    #                 "type": "string", 
    #                 "description": "Search query"
    #                 },
    #             "imo": {
    #                 "type": "string",
    #                 "description": "IMO number of the vessel to filter casefiles. REQUIRED when vessel name is known or mentioned in the user query.Use get_vessel_details tool first to convert vessel name to IMO number. "
    #                 },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number to search results(casefiles) to return per page (default is 10)."
    #             },
    #             "page": {
    #                 "type": "number",
    #                 "description": "Page number of results to return (starts at 1, default is 1)."
    #             }
    #         },
    #         "required": ["query"]
    #     }
    # ),
    types.Tool(
        name="smart_casefile_search",
        description=(
            "Universal, adaptive search tool for vessel case-files. "
            "Supports free-text semantic search, keyword search, and fine-grained filtering "
            "by vessel, category, importance, plan status, and date-range. "
            "\n\n"
            "✔️ If the user mentions a vessel **name**, ALWAYS:\n"
            "   1. Call `get_vessel_details` to convert that name to its IMO number.\n"
            "   2. Pass the returned IMO to the `filters.imo` parameter so that only "
            "      case-files for the correct vessel are returned.\n"
            "\n"
            "Typical queries:\n"
            "  • \"Overheating incidents on LNG Aurora\"\n"
            "  • \"hull inspection findings category:structural importance:high\"\n"
            "  • \"latest updated case-files for IMO 9321483 after 01/01/2025\"\n"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural-language query. Leave blank to browse all case-files for the "
                        "given filters. Example: 'main engine vibration root cause'"
                    )
                },
                "search_type": {
                    "type": "string",
                    "description": (
                        "Search strategy:\n"
                        "  • 'semantic'  → vector search on the `embedding` field for conceptual matching\n"
                        "  • 'keyword'   → traditional keyword match on indexed text fields\n"
                        "Choose automatically based on the user's intent; default is 'semantic'."
                    ),
                    "enum": ["semantic", "keyword"],
                    "default": "semantic"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to narrow results",
                    "properties": {
                        "imo": {
                            "type": "integer",
                            "description": (
                                "IMO number for vessel-specific searches. **Required** whenever the "
                                "user's query refers to a specific vessel name (convert via "
                                "`get_vessel_details`)."
                            )
                        },
                        "vessel_name": {
                            "type": "string",
                            "description": (
                                "Vessel name (case-insensitive). Used only when IMO is not yet known; "
                                "tool will internally resolve name→IMO."
                            )
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "General",
                                "LocationAndCargoActivity",
                                "sire",
                                "loReport",
                                "internalAudit",
                                "vir",
                                "FleetAlert",
                                "SmartShipAlert",
                                "fleetAlert",
                                "smartShipAlert",
                                "locationAndCargoActivity",
                                "classSurveyAndCertificateStatus"
                            ],
                            "description": "Category tag (must match one of the enum values)."
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["Medium", "Low", "High"],
                            "description": "Importance of the case file (must be one of: Medium, Low, High)"
                        },
                        "from_date": {
                            "type": "string",
                            "description": (
                                "Include case-files with `lastCasefileUpdateDate` **on or after** this "
                                "date (dd/mm/yyyy)."
                            )
                        },
                        "to_date": {
                            "type": "string",
                            "description": (
                                "Include case-files with `lastCasefileUpdateDate` **up to** this date "
                                "(dd/mm/yyyy)."
                            )
                        }
                    },
                    "additionalProperties": False
                },
                "sort_by": {
                    "type": "string",
                    "description": (
                        "Sort order:\n"
                        "  • 'recent'                  → `lastCasefileUpdateDate` desc (default)\n"
                        "  • 'oldest'                  → `lastCasefileUpdateDate` asc\n"
                        "  • 'importance_score_desc'   → `importance_score` desc\n"
                        "  • 'importance_score_asc'    → `importance_score` asc"
                    ),
                    "enum": [
                        "recent",
                        "oldest",
                        "importance_score_desc",
                        "importance_score_asc"
                    ],
                    "default": "recent"
                },
                "max_results": {
                    "type": "number",
                    "description": "Number of results to return (1-20)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10
                },
                "page": {
                    "type": "number",
                    "description": "Results page (1-based)",
                    "minimum": 1,
                    "default": 1
                }
            },
            "required": [],
            "additionalProperties": False
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
tool_definitions = typesense_tools + mongodb_tools + document_parser_tools + general_tools
