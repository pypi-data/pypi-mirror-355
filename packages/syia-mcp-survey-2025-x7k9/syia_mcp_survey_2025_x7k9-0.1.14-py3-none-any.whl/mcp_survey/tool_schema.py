from mcp_survey.databases import *
import mcp.types as types

# Typesense tool definitions for mcp_survey

typesense_tools = [
    #     types.Tool(
    #     name="certificate_table_search",
    #     description="[FALLBACK TOOL] Search the certificate collection in Typesense. It is mandatory to get the schema of the collection first using **get_table_schema** tool, then use the schema to search the required collection.  Use this tool when other more specialized tools have failed to provide sufficient information or when you want to search the certificate collection for a specific keyword or when more data is needed for any trend analysis that needs to be done. This is a generic search tool with less targeted results than purpose-built tools. Example question : Get me the expiry date for <certificate name> for <vessel>",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search",
    #                 "enum": ["certificate"]
    #             },
    #             "query": {
    #                 "type": "object",
    #                 "description": "Query parameters for the search"
    #             }
    #         },
    #         "required": ["collection", "query"]
    #     }
    # ),
    # types.Tool(
    #     name="certificate_table_search",
    #     description="[FALLBACK TOOL] Searches ship certificates, surveys, CMS, COC, and IHM records database containing expiry dates, issuing authorities, status, validity windows and links to the certificates. Use when other certificate tools do not give sufficient information or for keyword searches across multiple fields. Always get the schema first using the get_certificate_table_schema tool. Example question : Get me the expiry date for <certificate name> for <vessel>",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search.",
    #                 "enum": ["certificate"]
    #             },
    #             "query": {
    #                 "type": "object",
    #                 "description": "Query object to send to Typesense's search endpoint.",
    #                 "properties": {
    #                     "q": {
    #                         "type": "string",
    #                         "description": "Search string. Use '*' to match all records."
    #                     },
    #                     "query_by": {
    #                         "type": "string",
    #                         "description": (
    #                             "Comma-separated list of fields to apply the `q` search on. "
    #                             "Example: 'field1,field2'."
    #                         )
    #                     },
    #                     "filter_by": {
    #                         "type": "string",
    #                         "description": (
    #                             "Filter expression using Typesense syntax. Use ':' for equality, '<'/'>' for ranges. "
    #                             "Combine multiple conditions using '&&' or '||'. "
    #                             "Example: 'imo:<imo_number> && type:<certificate_type> && daysToExpiry:<cutoff_timestamp>'"
    #                         )
    #                     },
    #                     "include_fields": {
    #                         "type": "string",
    #                         "description": (
    #                             "Comma-separated list of fields to include in the results. "
    #                             "Example: 'field1,field2,field3'."
    #                         )
    #                     },
    #                     "per_page": {
    #                         "type": "integer",
    #                         "description": "Number of results to return per page, defaults to 10"
    #                     }
    #                 },
    #                 "required": ["q", "query_by"]
    #             }
    #         },
    #         "required": ["collection", "query"]
    #     }
    # ),
    types.Tool(
        name="smart_certificate_search",
        description=(
        "Universal search tool for vessel certificates and compliance documents. "
        "Primary tool for querying certificate data across the fleet."
        "Handles everything from specific certificate lookups to compliance overviews and browsing expired or soon-to-expire records."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                "type": "string",
                "description": (
                        "Natural language or keyword query. This is matched against the fields certificateSurveyEquipmentName and issuingAuthority. Use '*' to match all records."
                ),
                "default": "*"
            },
            "filters": {
                "type": "object",
                "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
                "properties": {
                    "imo": {
                        "type": "number",
                        "description": "IMO number of the vessel"
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of records to be returned, CERTIFICATE for certificates, CMS for continuous machinery survey, COC for condition of class, IHM for inventory of hazardous materials, SURVEY for survey",
                        "enum": ["CERTIFICATE", "CMS", "COC", "IHM", "SURVEY"]
                    },
                    "certificateSurveyEquipmentName": {
                        "type": "string",
                        "description": "Exact scope or equipment name related to the certificate"
                    },
                    "issuingAuthority": {
                        "type": "string",
                        "description": "Authority that issued the certificate (e.g., 'DNV', 'ABS')"
                    },
                    "certificateNumber": {
                        "type": "string",
                        "description": "Exact certificate number"
                    },
                    "currentStatus": {
                        "type": "string",
                        "description": "Current lifecycle status of the certificate",
                        "enum": [ "IN ORDER", "IN WINDOW", "EXPIRED" ]
                    },
                    "isExtended": {
                        "type": "boolean",
                        "description": "Filter for certificates that have been extended"
                    },
                    "dataSource": {
                        "type": "string",
                        "description": "Data source for the certificate, MMPL and Shippalm are company ERP systems, Class is the classification society",
                        "enum": ['Class', 'MMPL', 'ShippalmV2', 'ShippalmV3']
                    },
                    "daysToExpiry_range": {
                        "type": "object",
                        "description": "Filter by number of days remaining until expiry (negative values include expired)",
                        "properties": {
                            "min_days": {
                                "type": "number",
                                "description": "Minimum days until expiry"
                            },
                            "max_days": {
                                "type": "number",
                                "description": "Maximum days until expiry"
                            }
                        }
                    },
                    "issueDate_range": {
                        "type": "object",
                        "description": "Filter by issue date of the certificate",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    },
                    "expiryDate_range": {
                        "type": "object",
                        "description": "Filter by expiry date of the certificate",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    }
                }
            },
            "sort_by": {
                "type": "string",
                "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                "enum": ["relevance", "expiryDate", "issueDate", "daysToExpiry"],
                "default": "relevance"
            },
            "sort_order": {
                "type": "string",
                "description": "Sorting order of the results",
                "enum": ["asc", "desc"],
                "default": "asc"
            },
            "max_results": {
                "type": "number",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": ["query"],
        "additionalProperties": False
        }
    ),
    # types.Tool(
    #     name="get_survey_casefiles",
    #     description="Use this tool to fetch all vessel-related case files that mention the word 'survey','class','certificate','IHM','CMS','COC' and were sent within a recent time window:\n1. mention the lookback hours in the request. this is the hours to look back for the survey related casefiles. Example Question: Give me list of Survey related casefiles in last 24 hours",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo","lookback_hours", "query_keyword"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "IMO number of the vessel"
    #             },
    #             "lookback_hours": {
    #                 "type": "integer",
    #                 "description": "Lookback hours in the request"
    #             },
    #             "query_keyword": {
    #                 "type": "string",
    #                 "description": "The keyword to be searched in the casefiles"
    #             },
    #             "per_page": {
    #                 "type": "integer",
    #                 "description": "Number of casefiles to return per page"
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    # types.Tool(
    #    name="get_survey_emails",
    #    description="Returns vessel-related email messages that are tagged as 'class' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'class' covers all emails related to class, survey, certificates, IHM",
    #    inputSchema={
    #        "type": "object",
    #        "required": ["imo", "tag"],
    #        "properties": {
    #            "imo": {
    #                "type": "string",
    #                "description": "IMO number of the vessel"
    #            },
    #            "lookback_hours": {
    #                "type": "integer",
    #                "description": "Rolling window size in hours (e.g., 24 = last day).Optional - Only to used if user asks for a specific window period"
    #            },
    #            "tag":{
    #                "type": "string",
    #                "description": "The tag to be searched in the emails",
    #                "enum": ["class"]
    #            },
    #            "per_page": {
    #                "type": "number",
    #                "description": "Number of emails to return per page (default is 50)."
    #            }
    #        },
    #        "additionalProperties": False
    #    }

    # ),
    types.Tool(
        name="list_extended_certificate_records",
        description="Use this tool to get the list of  certificate-related records for a vessel that have been **officially extended** (that is, `isExtended=true`).1. Read the vessel's IMO (or name) from the user's request.2. Optionally read one or more record **types** to narrow the search.  Valid values are: CERTIFICATE, CMS, COC, IHM, SURVEY.  If no type is supplied the tool will return all types.3. Query the *certificate* collection combining the vessel's `imo`, the fixed filter `isExtended:true`, and—if provided—the `type` filter from step 2.4. Optionally let the caller specify how many results to show per page.Example question: 'Give me a list of surveys, CoC, IHM, CMS or certificates for VESSEL_NAME that have been extended.'",
        inputSchema=  {
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                },
                "recordType": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CERTIFICATE", "CMS", "COC", "IHM", "SURVEY"]
                    },
                    "description": "Optional record type (use one of the enum values; omit to include all types).Multiple types to be given as comma separated values"
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to return per page (default is 250)."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_records_expiring_within_days",
        description="Use this tool to get the list of  **certificate-related records** (CERTIFICATE, CMS/CSM, COC, IHM, or SURVEY) for a vessel that will expire within the next **N days**. 1. Read the vessel's IMO (or name) and the desired record **type** from the user's request.  The type must be one of the allowed enum values: CERTIFICATE, CMS, COC, IHM, SURVEY.2. Read the day horizon **X** (e.g., 90) and apply the filter `daysToExpiry:<N` so only records whose expiry or due date is less than N days away are returned.3. Query the *certificate* collection with three combined filters: the vessel's `imo`, the selected `type`, and the `daysToExpiry` limit from step 2.4. Optionally let the caller specify how many results to show per page.Example question: 'Show all Certificate items that will expire in the next 90 days for VESSEL_NAME.'",
        inputSchema=   {
            "type": "object",
            "required": ["imo", "recordType", "daysToExpiry"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                },
                "recordType": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CERTIFICATE", "CMS", "COC", "IHM", "SURVEY"]},
                    "description": "Record type to filter. Multiple types to be given as comma separated values"
                },
                "daysToExpiry": {
                    "type": "number",
                    "description": "Number of days remaining for certificate , survey, CMS or COC to expire.Upper limit in days (X) for the remaining time to expire"
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to return per page (default is 250)."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_records_by_status",
        description="Return survey, certificate, or continuous-machinery-survey (CSM/CMS) records for one or more vessels whose `status` matches specific life-cycle states (e.g., EXPIRED or IN_WINDOW).**How to invoke**  1. Populate `imo` with at least one seven-digit integer (IMO number).2. Select one or more `recordType` values  [CERTIFICATE, CSM, COC, IHM, SURVEY].3. Select one or more `status` values  [EXPIRED, IN_WINDOW, IN_ORDER].4. (Optional) Tune `perPage` (default = 250, max = 500).All supplied filters are combined with logical AND semantics.",
        inputSchema=  {
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number for the target vessel."
                },
                "recordType": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CERTIFICATE", "CSM", "COC", "IHM", "SURVEY"]
                    },
                    "description": "Record category filter. Multiple selections permitted."
                },
                "status": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["IN_ORDER", "IN_WINDOW", "EXPIRED"]
                    },
                    "description": "Lifecycle state filter for the record."
                },
                "perPage": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 250,
                    "description": "Upper bound on records returned per page."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "required": ["imo", "recordType"],
            "additionalProperties": False
        }
    )
]

# MongoDB tool definitions for mcp_survey

mongodb_tools = [
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
    ),
    # types.Tool(
    #     name="get_certificate_table_schema",
    #     description="This tool retrieves Typesense certificate table schema and instructions on how to query the certificate table for a specific category.",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["category"],
    #         "properties": {
    #             "category": {
    #                 "type": "string",
    #                 "description": "The category for which to retrieve the Typesense schema (e.g., purchase, voyage, certificates).",
    #                 "enum": ["certificate"]
    #             },
    #             "session_id": {
    #                 "type": "string",
    #                 "description": "Session ID for tracking client sessions, if available"
    #             }
    #         }            
    #     }
    # ),
    types.Tool(
        name="get_user_associated_vessels",
        description="Retrieves a list of vessels associated with a specific user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The ID of the user to find associated vessels for."
                }
            },
            "required": ["user_id"]
        }
    ),
    types.Tool(
        name="get_class_survey_report",
        description="Retrieves Class Survey Status Report pdf link for a specific vessel.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_class_certificate_status",
        description="Use this tool to get an overview of a vessel's statutory certificates based on data from Class website. it informs  whether all certificates are in order or if any are due or overdue.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_class_survey_status",
        description="use this tool to get an overview of a vessel's statutory surveys based on data from the Class website. it informs whether all surveys are in order or if any are due, in window or overdue",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_coc_notes_memo_status",
        description="Use this tool to get details of  CoCs, notes, and memos for the vessel including issue date, due date and status from Class Website.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_vessel_dry_docking_status",
        description="Use this tool to get the information onNext periodical survey (Annual/Intermediate/Special) due date, type of survey, window period, remaining days etc.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_next_periodical_survey_details",
        description="Retrieves Next Periodical Survey details for a specific vessel.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_cms_items_status",
        description="Use this tool to get an overview of a vessel's CMS (Continuous Survey of Machinery) items based on data from Class website. it informs  whether all CMS Items are in order or if any are due or overdue.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_expired_certificates_from_shippalm",
        description="Use this tool to get an overview of a vessel's certificates based on data from the ERP system, Ship Palm. It informs  whether all certificates are in order or if any are due or overdue.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_vessel_class_by_imo",
        description="Fetch the class (classification society) recorded for a vessel. The tool looks up the document whose `imo` field matches the supplied IMO number in the Typesense collection `fleet-vessel-lookup`, and returns the value of its `class` field (plus the IMO for reference).",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "number",
                    "description": "IMO number of the vessel."
                }
            },
            "additionalProperties": False
        }
    ),
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

class_tools = [
    types.Tool(
        name="class_ccs_survey_status_download",
        description="Downloads Survey Status Report from CCS website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_nk_survey_status_download",
        description="Downloads Survey Status Report from NK website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_kr_survey_status_download",
        description="Downloads Survey Status Report from KR website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_dnv_survey_status_download",
        description="Downloads Survey Status Report from DNV website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_lr_survey_status_download",
        description="Downloads Survey Status Report from LR website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_bv_survey_status_download",
        description="Downloads Survey Status Report from BV website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    ),
    types.Tool(
        name="class_abs_survey_status_download",
        description="Downloads Survey Status Report from ABS website for a vessel and returns download path",
        inputSchema={
            "type": "object",
            "properties": {
                "vessel_name": {"type": "string", "description": "Name of the vessel"}
            },
            "required": ["vessel_name"]
        },
        returns="str"
    )
]

casefile_tools = [
# Tool 1: Write Casefile Data
    types.Tool(
        name="write_casefile_data",
        description=(
            "Creates or updates casefile-related data. "
            "Supports two distinct operations:\n"
            "- write_casefile: Create or update casefile metadata (e.g., summary, title, importance).\n"
            "- write_page: Add or update a page under an existing casefile, including content and indexing."
            "Only pass arguments explicitly required or allowed for the chosen operation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["write_casefile", "write_page"],
                    "description": (
                        "Specifies the writing operation: 'write_casefile' for creating new casefile or 'write_page' for page content of already existing casefile."
                    )
                },
                "casefile_url":{
                    "type": "string",
                    "description": (
                        "The unique identifier of the casefile,  direct casefile url link."
                        "Required for 'write_page'."
                    )
                },
                "casefileName": {
                    "type": "string",
                    "enum":["Class Survey and Certificate Status"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["classSurveyAndCertificateStatus"],
                    "description": (
                        "Required for 'write_casefile' . Category of the casefile"
                    )
                },
                "currentStatus": {
                    "type": "string",
                    "description": (
                        "<review the casefile and plan to create current status in one line, highlighting keywords>"
                        "Required for 'write_casefile': Current status of the casefile, it will be of 4-5 words."
                        "Required for 'write_page': update or kept it same status of the casefile based on recent received email. it willbe of 4-5 words."
                    )
                },
                "casefileSummary": {
                    "type": "string",
                    "description": (
                        "Required for 'write_casefile'. Summary or high-level description of the casefile.\n"
                        "Optional for 'write_page': can provide updated summary if needed."
                    )
                },
                "importance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "It will show the importance of the casefile reference for the urgency and importance of the matter in the casefile."
                        "Required for 'write_casefile'. Importance score of the casefile (0–100).\n"
                        "required for 'write_page': can provide an updated score based on the new email content added to the casefile."
                    )
                },
                "imo": {
                    "type": "integer",
                    "description": (
                        "Required for 'write_casefile'. IMO number of the associated vessel."
                    )
                },
                "role": {
                    "type": "string",
                    "enum": ["incident", "legal", "regulatory", "other"],
                    "description": (
                        "Required for 'write_casefile'. Role/category of the casefile."
                    )
                },
                "summary": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'. Detailed content or summary of the new page."
                    )
                },
                "topic": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'.It is of 4-8 words aboyt what this document is about."
                    )
                },
                "facts": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'..It will  have the highlighted facts/information from the database."
                    )
                },
                "detailed_report":{
                    "type": "string",
                    "description": (
                        "Required for 'write_page'. It will have the detailed report of the casefile in markdown format."
                    )
                },
                # "mailId": {
                #     "type": "string",
                #     "description": (
                #         "Required for 'write_page'. Email ID associated with the page content."
                #     )
                # },
                # "tags": {
                #         "type": "array",
                #         "items": {
                #             "type": "string",
                #             "enum": [
                #                 "Itinerary", "Agent Details", "LO Report", "FO Report", "Performance Report",
                #                 "Workdone Report", "Vessel Inspection", "SIRE Inspection", "Internal Audit",
                #                 "Defect", "Monthly Budget", "Purchase", "Survey", "Crew", "Maintenance", "Charter Party"
                #             ]
                #         },
                #         "description": (
                #             "Optional array of tags to categorize the email case file. Useful for organizing vessel-related content.\n"
                #             "- Itinerary: ETA/ETB/ETD details and voyage plans.\n"
                #             "- Agent Details: Vessel agent contact info.\n"
                #             "- Defect: Equipment issues not related to audits or inspections.\n"
                #             "Other tags are standard and self-explanatory"
                #         )
                #     }
                "links": {
                    "type": "array",
                    "items": {  
                        "type": "string"
                    },
                    "description": (
                        "Required for 'write_page'. Relevent links you want to add to the case file."
                    )
                }
            },
            "required": ["operation"],
            "additionalProperties": False
        }
    ),

     types.Tool(
        name="retrieve_casefile_data",
        description=(
            "Retrieves data from casefiles. "
            "Supports the following operations:\n"
            "- get_casefiles: List all casefiles for a vessel matching a text query.\n"
            "- get_casefile_plan: Retrieve the latest plan associated with a specific casefile.\n"
            "Only pass arguments explicitly required or allowed for the chosen operation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["get_casefiles","get_casefile_plan"],
                    "description": "Specifies the retrieval operation."
                },
                "imo": {
                    "type": "integer",
                    "description": (
                        "Required for 'get_casefiles'. IMO number of the vessel."
                    )
                },
                 "category": {
                    "type": "string",
                    "enum": ["classSurveyAndCertificateStatus"],
                    "description": (
                        "Required for 'get_casefiles'. Category of the casefile."
                    )
                },
                "casefile_url": {
                "type": "string",
                "description": "The unique identifier of the casefile,  direct casefile url link. Required for operation get_casefile_plan."
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Optional for 'get_casefiles'. search query to filter casefiles based on the context and user query."
                    )
                },
                "min_importance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "Optional for 'get_casefiles'. Filter results with importance score ≥ this value."
                    )
                },
                "pagination": {
                    "type": "integer",
                    "default": 1,
                    "description": (
                        "optional for 'get_casefiles'. Page number for paginated results."

                    )
                },
                "page_size": {
                    "type": "integer",
                    "default": 10,
                    "description": (
                        "Optional for 'get_casefiles'. Number of results per page."
                    )
                }
            },
            "required": ["operation"]
        }
    )


]
# Combined tools for compatibility
tool_definitions = typesense_tools + mongodb_tools +  document_parser_tools + general_tools + class_tools + casefile_tools
