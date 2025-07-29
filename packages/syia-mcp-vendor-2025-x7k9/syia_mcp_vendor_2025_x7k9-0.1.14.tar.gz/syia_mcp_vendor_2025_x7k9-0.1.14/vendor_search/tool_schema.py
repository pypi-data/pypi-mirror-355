from vendor_search.databases import *
import mcp.types as types

# Typesense tool definitions for mcp_vendor

typesense_tools = [
        types.Tool(
        name="typesense_query",
        description="Search a Typesense collection, use this if you want to search by any other field, or want to create custom queries",
        inputSchema={
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "Name of the collection to search"
                },
                "query": {
                    "type": "object",
                    "description": "Query parameters for the search"
                }
            },
            "required": ["collection", "query"]
        }
    ),
    types.Tool(
        name = "find_relevant_vendors",
        description = "Searches for vendors by matching on service, location, and/or name. Supports synonym expansion and relevance-based ranking to find the most suitable vendors.",
        inputSchema = {
            "type": "object",
            "properties": {
                "vendorName": {
                    "type": "string",
                    "description": "Name of the vendor the user is looking for if any"
                },
                "service": {
                    "type": "string",
                    "description": "Service the vendor provides the user is looking for if any"
                },
                "locationRegion": {
                    "type": "string",
                    "description": "Location of the vendor the user is looking for if any"
                }
            },
            "required": []
        }
    ),
    types.Tool(
        name = "get_vendor_contact_details",
        description = "Returns contact information (address, phone number, email) for a specific vendor by name. Use this tool when the user is asking for a vendor's contact information or how to reach a vendor.",
        inputSchema = {
            "type": "object",
            "properties": {
                "vendorName": {
                    "type": "string",
                    "description": "Name of the vendor the user is looking for"
                }
            },
            "required": ["vendorName"]
        }
    )
]


# MongoDB tool definitions for mcp_vendor

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
                    "description": "must set as vendor4",
                    "enum": ["vendor4"]
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
        description="Use this tool to parse a document link and local file. The tool will parse the document and return the text content.",
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