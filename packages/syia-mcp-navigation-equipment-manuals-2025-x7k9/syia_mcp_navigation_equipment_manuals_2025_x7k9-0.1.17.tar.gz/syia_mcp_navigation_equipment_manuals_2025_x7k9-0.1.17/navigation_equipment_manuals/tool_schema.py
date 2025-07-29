from navigation_equipment_manuals.databases import *
import mcp.types as types 

# Typesense tool definitions for mcp_pms

typesense_tools = [  
            types.Tool(
                name = "smart_navigation_manual_search",
                description = (
                    "Universal search tool for navigation equipment manuals. "
                    "This is the primary tool for finding any information in the manual database. "
                    "It intelligently adapts search strategy based on query intent and can handle "
                    "everything from specific lookups to general browsing."
                ),
                inputSchema = {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural language search query. Leave empty for browsing mode. "
                                "Examples: 'radar calibration procedure', 'AIS not showing targets', "
                                "'power consumption specifications'"
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
                                "maker": {
                                    "type": "string",
                                    "description": "Equipment manufacturer name",
                                    "enum": ["FURUNO", "JRC", "SIMRAD", "KODEN", "SPERRY MARINE", "SAM ELECTRONICS", "SAILOR", 
                                             "SAAB", "RAYTHEON", "RAYTHEON ANSCHUTZ", "ANSCHUTZ", "SKIPPER", "NINGLU", "INMARSAT", 
                                             "DANELEC MARINE", "SPEERY", "JMC", "TOKIMEC", "AMI", "SAMYUNG NAVTEX", "TOKYO KEIKI", 
                                             "HYUNDAI","STRATUM FIVE SSAS", "SM ELECTRICS", "MARTEK", "JOTRON", "INTELLIAN", 
                                             "FBB LAUNCH PAD", "DANLEC", "STX", "RM YOUNG"]
                                },
                                "model": {
                                    "type": "string",
                                    "description": "Specific equipment model number"
                                },
                                "equipment": {
                                    "type": "string",
                                    "description": "Type of navigation equipment",
                                    "enum": ["AIS", "RADAR", "MF-HF", "ECDIS", "SPEED LOG", "BNWAS", "GPS", "GYRO", "AUTO PILOT", 
                                             "NAVTEX", "ECHO-SOUNDER", "VDR", "VHF", "SATC", "INMARSAT-C", "FBB", "SSAS", "ANEMOMETER", 
                                             "SATELLITE LOG", "WEATHER FAX", "PUBLIC ALARM AND TALK BACK SYSTEM"]
                                },
                                "document_name": {
                                    "type": "string",
                                    "description": "Exact name of the manual document",
                                },
                                "document_type": {
                                    "type": "string",
                                    "description": "Category of manual",
                                    "enum": ["Operation Manual", "Installation Manual", "Instruction Manual", "Service Manual", "Troubleshooting", 
                                             "MMPL Operation Manual", "MMPL Installation Manual", "MMPL Instruction Manual", "MMPL Service Manual", 
                                             "MMPL Troubleshooting"]
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
            # Navigation Manual Tools
            types.Tool(
                name="list_equipment_manufacturers",
                description="Retrieves a list of all manufacturers for navigation equipment in the database, can be used to check if a specific manufacturer is available and by what name it is stored in the database.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_navigation_equipment_types",
                description="Retrieves a list of navigation equipment, Returns the equipment categories like rdar ECDIS, GPS autopilot etc.Use this tool to check if a specific equipment type is available and verify the exact naming convention used in the database for queries.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "maker": {"type": "string",
                                  "description": "Optional. The specific manufacturer of the navigation equipment to filter by."},
                                  "enum": ["FURUNO", "JRC", "SIMRAD", "KODEN", "SPERRY MARINE", "SAM ELECTRONICS", "SAILOR", 
                                             "SAAB", "RAYTHEON", "RAYTHEON ANSCHUTZ", "ANSCHUTZ", "SKIPPER", "NINGLU", "INMARSAT", 
                                             "DANELEC MARINE", "SPEERY", "JMC", "TOKIMEC", "AMI", "SAMYUNG NAVTEX", "TOKYO KEIKI", 
                                             "HYUNDAI","STRATUM FIVE SSAS", "SM ELECTRICS", "MARTEK", "JOTRON", "INTELLIAN", 
                                             "FBB LAUNCH PAD", "DANLEC", "STX", "RM YOUNG"]
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="list_navigation_equipment_models",
                description="Retrieves a list of navigation equipments by maker and equipment type. This requires exact names for both maker and/or equipment.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "maker": {"type": "string",
                                  "description": "Optional. The specific manufacturer of the navigation equipment to filter by."},
                        "equipment": {"type": "string",
                                      "description": "Optional. The specific equipment type to filter by."},
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="find_equipment_manuals",
                description=("Retrieves a list of all manuals available in the database for a specific maker, model, and equipment type. "
                             "Must provide at least one of the parameters maker, model, or equipment. Use other tools to get the maker, model, or equipment type before using this tool."),
                inputSchema={
                    "type": "object",   
                    "properties": {
                        "maker": {"type": "string",
                                  "description": "The specific manufacturer of the navigation equipment to filter by.",
                                  "enum": ["FURUNO", "JRC", "SIMRAD", "KODEN", "SPERRY MARINE", "SAM ELECTRONICS", "SAILOR", 
                                             "SAAB", "RAYTHEON", "RAYTHEON ANSCHUTZ", "ANSCHUTZ", "SKIPPER", "NINGLU", "INMARSAT", 
                                             "DANELEC MARINE", "SPEERY", "JMC", "TOKIMEC", "AMI", "SAMYUNG NAVTEX", "TOKYO KEIKI", 
                                             "HYUNDAI","STRATUM FIVE SSAS", "SM ELECTRICS", "MARTEK", "JOTRON", "INTELLIAN", 
                                             "FBB LAUNCH PAD", "DANLEC", "STX", "RM YOUNG"]
                                  },
                        "model": {"type": "string",
                                  "description": "The specific model name or number of the navigation equipment to filter by."},
                        "equipment": {"type": "string",
                                      "description": "The specific equipment type to filter by.",
                                      "enum": ["AIS", "RADAR", "MF-HF", "ECDIS", "SPEED LOG", "BNWAS", "GPS", "GYRO", "AUTO PILOT", 
                                               "NAVTEX", "ECHO-SOUNDER", "VDR", "VHF", "SATC", "INMARSAT-C", "FBB", "SSAS", "ANEMOMETER", 
                                               "SATELLITE LOG", "WEATHER FAX", "PUBLIC ALARM AND TALK BACK SYSTEM"]
                                      },
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="search_manual_content",
                description="Retrieves information corresponding to user query using semantic search from navigation manuals based on the maker, equipment, model, or manual type, whichever available. Pass an empty string if not available, that field will not be filtered. Filters, if passed, should be exact names.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "maker": {"type": "string",
                                  "description": "Optional. The specific manufacturer of the navigation equipment. Examples: 'Simrad', 'JMA'."},
                        "model": {"type": "string",
                                  "description": "Optional. The specific model name or number of the navigation equipment. Examples: 'GP-90', 'FMD-3200', 'JMA-1030'."},
                        "equipment": {"type": "string",
                                      "description": "Optional. The specific equipment type of the navigation equipment. Examples: 'GPS', 'Radar', 'Autopilot'."},
                        "manual_type": {"type": "string",
                                        "description": "Optional. Type of manual required. Options: installation, operation, or service."},
                        "user_query": {"type": "string",
                                      "description": "Optional. Natural language query for vector search. If provided, this will be used for semantic search using document embeddings."}
                    },
                    "required": []
                }
            ),

        ]


# MongoDB tool definitions for mcp_pms

mongodb_tools = [
    #   types.Tool( 
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

tool_definitions = typesense_tools + mongodb_tools + general_tools
