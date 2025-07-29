from .databases import *
import mcp.types as types

# Typesense tool definitions for mcp_pms

typesense_tools = [
    # types.Tool(
    #     name="defect_table_query",
    #     description="[FALLBACK TOOL] Search the defect collection in Typesense. It is mandatory to get the schema of the collection first using **get_table_schema** tool, then use the schema to search the required collection.  Use this tool when other more specialized tools have failed to provide sufficient information or when you want to search the defect collection for a specific keyword or when more data is needed for any trend analysis that needs to be done. This is a generic search tool with less targeted results than purpose-built tools. Example question : Get me list of defects for <vessel> from MOU website ",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search",
    #                 "enum": ["defect"]
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
    #     name="defect_table_query",
    #     description="[FALLBACK TOOL] Searches defect records database containing inspection findings, PSC/SIRE/audit results, risk categories, detention status, and rectification tracking from multiple sources (OCIMF, CLASS, PSC, SHIPPALM). Use when other defect tools do not give sufficient information or for keyword searches or for any data retrieval for trend analysis . Always get the schema first using the get_defect_table_schema tool . Example: Find PSC defects from Paris MOU for <vessel>",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search.",
    #                 "enum": ["defect"]
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
    #                         "description": "Comma-separated list of fields to apply the `q` search on. Example: 'field1,field2'."
    #                     },
    #                     "filter_by": {
    #                         "type": "string",
    #                         "description": "Filter expression using Typesense syntax. Use ':' for equality, '<'/'>' for ranges. Combine multiple conditions using '&&' or '||'. Example: 'imo:<imo_number> && type:<certificate_type> && daysToExpiry:<cutoff_timestamp>'"
    #                     },
    #                     "include_fields": {
    #                         "type": "string",
    #                         "description": "Comma-separated list of fields to include in the results. Example: 'field1,field2,field3'."
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
        name="smart_defect_search",
        description=(
            "Universal search tool for vessel defects, inspection findings, and compliance issues. "
            "Primary tool for querying defect data across the fleet from multiple sources (SHIPPALM, OCIMF, CDI, CLASS, PSC). "
            "Handles everything from specific defect lookups to inspection overviews and browsing open, overdue, or closed defects."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language or keyword query. This is matched against the fields finding, inspectionType, reportType, inspectedBy, inspectionLocation and inspectingCompany. Use '*' to match all records.",
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
                        "vesselName": {
                            "type": "string",
                            "description": "Exact or partial name of the vessel"
                        },
                        "source": {
                            "type": "string",
                            "description": "Data source from which the defect record was taken",
                            "enum": ["SHIPPALM", "OCIMF", "CDI", "CLASS", "PSC"]
                        },
                        "inspectionType": {
                            "type": "string",
                            "description": "Specific type of inspection carried out (e.g., 'PSC INSPECTION', 'SIRE INSPECTION', 'INTERNAL AUDIT ISM/MLC/ISO')"
                        },
                        "reportType": {
                            "type": "string",
                            "description": "Type of report used in the inspection (e.g., 'DEFICIENCY', 'NEAR MISS REPORT', 'NC/NON CONFORMITY REPORT')"
                        },
                        "stage": {
                            "type": "string",
                            "description": "Current stage of the defect within the inspection process",
                            "enum": ["OPEN", "CLOSED", "OPEN OVERDUE"]
                        },
                        "currentStatus": {
                            "type": "string",
                            "description": "Detailed status of the inspection or defect (e.g., 'APPROVED', 'IN PROGRESS', 'CLOSED')"
                        },
                        "riskCategory": {
                            "type": "string",
                            "description": "Risk level assigned to the defect",
                            "enum": ["Low", "Medium", "High"]
                        },
                        "mouWebsite": {
                            "type": "string",
                            "description": "Memorandum of Understanding (MOU) region for PSC inspections (e.g., 'PARIS MOU', 'TOKYO MOU')"
                        },
                        "detention": {
                            "type": "string",
                            "description": "Indicates whether the vessel was detained during PSC inspection",
                            "enum": ["YES", "NO"]
                        },
                        "isExtended": {
                            "type": "boolean",
                            "description": "Filter for defects that have had their rectification deadline formally extended"
                        },
                        "latestReport": {
                            "type": "boolean",
                            "description": "Filter for records belonging to the latest inspection/report only"
                        },
                        "findingsReference": {
                            "type": "string",
                            "description": "Exact identification number of the finding or inspection"
                        },
                        "reportDate_range": {
                            "type": "object",
                            "description": "Filter by date the defect was reported",
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
                        "closingDate_range": {
                            "type": "object",
                            "description": "Filter by date the defect was rectified/closed",
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
                        "targetDate_range": {
                            "type": "object",
                            "description": "Filter by target deadline for rectifying the defect",
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
                    "enum": ["relevance", "reportDate", "closingDate", "targetDate", "isExtended", "latestReport"],
                    "default": "relevance"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sorting order of the results",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results to return",
                    "default": 25,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    ),
    # types.Tool(
    #     name="get_defect_emails",
    #     description="Returns vessel-related email messages that are tagged as 'defect' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'defect' covers all emails related to defects",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo", "lookbackHours", "tag"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string", 
    #                 "description": "The IMO number of the vessel"
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day)."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "The tag to be searched in the emails",
    #                 "enum": ["defect"]
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 50)."
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    # types.Tool(
    #     name="list_incident_emails",
    #     description="Returns vessel-related email messages that are tagged as 'incident' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'incident' covers all emails related to incidents",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo", "lookbackHours", "tag"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string", 
    #                 "description": "The IMO number of the vessel"
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day)."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "The tag to be searched in the emails",
    #                 "enum": ["incident"]
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 50)."
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    # types.Tool(
    #     name="list_inspection_emails",
    #     description="Returns vessel-related email messages that are tagged as 'inspection' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'inspection' covers all emails related to inspections",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo", "lookbackHours", "tag"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string", 
    #                 "description": "The IMO number of the vessel"
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day)."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "The tag to be searched in the emails",
    #                 "enum": ["inspection"]
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 50)."
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    # types.Tool(
    #     name="get_defect_casefiles",
    #     description="Use this tool to fetch all vessel-related case files that mention the word \"defect\", \"inspection\", \"detention\" and were sent within a recent time window:\n1. Take the current date-and-time (UTC).\n2. Subtract the desired look-back period (X hours or days) and get calculated_date_time.\n3. Query the caseFiles collection for case files whose lastCasefileUpdateDate is greater than the calculated_date_time **and** casefile field contains the keyword.\nProvide the vessel's IMO (or name) and the lookback hours; optionally set how many results you want per page. Example Question: Give me list of defect related case files in last 24 hours",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo", "lookbackHours", "query_keyword"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string", 
    #                 "description": "The IMO number of the vessel"
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day)."
    #             },
    #             "query_keyword": {
    #                 "type": "string",
    #                 "description": "The keyword to be searched in the case files (e.g., defect, inspection, detention)."
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of case files to return per page (default is 50)."
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    types.Tool(
        name="list_defects_by_stage",
        description="Use this tool to list defect (inspection-finding) records for a vessel that match one or more **stage** values (e.g., \"OPEN\", \"OPEN OVERDUE\", \"CLOSED\").\n\nHow it works:\n1. Identify the vessel by its IMO number (or name).\n2. Read the desired **stage** filter from the user's request. Enum values include \"OPEN\", \"OPEN OVERDUE\", \"CLOSED\", etc. You may pass a single value or a comma-separated list if the user asks for multiple stages.\n3. Query the *defect* collection combining the vessel's `imo` filter with the chosen `stage` filter(s).\n4. The tool returns comprehensive defect fields, including reference number, finding, risk category, corrective action, and key inspection dates.\n5. Optionally specify how many results to return per page.\n\nExample question: \"Give me a list of defects that are **overdue** for VESSEL_NAME.\" → use `imo=IMO_NUMBER`, `stage=\"OPEN OVERDUE\"`.",
        inputSchema={
            "type": "object",
            "required": ["imo", "stage"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "stage": {
                    "type": "string",
                    "description": "Stage value (or comma-separated list) to filter defects, e.g., \"OPEN\", \"OPEN OVERDUE\", \"CLOSED\".",
                    "enum": ["OPEN", "CLOSED", "OPEN OVERDUE"]
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
        name="list_defects_by_inspection_type",
        description="Use this tool to list defect (inspection-finding) records for a vessel that belong to a **specific inspection or audit type**—for example *INTERNAL AUDIT*, *SIRE INSPECTION*, or *PSC INSPECTION*. You may also, if needed, narrow the results to one of three **stage** values (OPEN, OPEN OVERDUE, or CLOSED).\n\nHow to use it\n1. Identify the vessel by its IMO number (or name).\n2. Select one or more of the allowed **inspectionType** enum values.\n3. (Optional) Provide a **stage** filter—choose ONE of \"OPEN\", \"OPEN OVERDUE\", or \"CLOSED\". Omit this field to retrieve all stages.\n4. Query the *defect* collection combining:\n   • the vessel's `imo`,\n   • `inspectionType` equal to the selected enum value, and\n   • if supplied, `stage` equal to the chosen stage.\n5. Optionally specify how many results you want per page.\n\nExample question: \"Open Internal Audit defects for VESSEL_NAME.\" → `imo = IMO_NUMBER`, `inspectionType = INTERNAL AUDIT`, `stage = OPEN`.",
        inputSchema={
            "type": "object",
            "required": ["imo", "inspectionType"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "inspectionType": {
                    "type": "string",
                    "description": "Inspection/Audit type to filter. Multiple types can be sent as comma separated values.",
                    "enum": [
                        "2ENG TOV AUDIT/SECOND ENGINEER TOV AUDIT",
                        "CARGO AND BALLAST AUDIT",
                        "CDI INSPECTION",
                        "CE TOV AUDIT/CHIEF ENGINEER TOV AUDIT",
                        "CHARTERERS INSPECTION",
                        "CLASS INSPECTION",
                        "COFF TOV AUDIT",
                        "DIRECTOR VISIT",
                        "DYNAMIC CARGO / BUNKER AUDIT",
                        "DYNAMIC MOORING / ANCHORING AUDIT",
                        "DYNAMIC NAVIGATION AUDIT",
                        "ENVIRONMENT AUDIT",
                        "EXTERNAL AUDIT",
                        "EXTERNAL ISM AUDIT",
                        "EXTERNAL ISPS AUDIT",
                        "EXTERNAL MLC INSPECTION",
                        "FLAG STATE INSPECTION",
                        "INTERNAL AUDIT",
                        "INTERNAL AUDIT ISM/MLC/ISO",
                        "INTERNAL AUDIT ISPS AUDIT",
                        "MANAGER VISIT",
                        "MSTR NAV AUDIT/MASTER NAVIGATIONAL AUDIT",
                        "MSTR TOV AUDIT/MASTER TOV AUDIT",
                        "NAVIGATION AUDIT",
                        "OTHER INSPECTION/AUDIT",
                        "OWNER'S INSPECTION",
                        "PORT HEALTH INSPECTION",
                        "PSC INSPECTION",
                        "REMOTE SHIP INSPECTION",
                        "RIGHTSHIP INSPECTION",
                        "SCMM",
                        "SIRE INSPECTION",
                        "SUPERINTENDENT VISIT",
                        "TERMINAL INSPECTION",
                        "USCG COC INSPECTION",
                        "VIR"
                    ]
                },
                "stage": {
                    "type": "string",
                    "enum": ["OPEN", "OPEN OVERDUE", "CLOSED"],
                    "description": "Optional stage filter (omit to include all stages)."
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
        name="list_defects_by_report_type",
        description="Use this tool to list defect / safety-management records for a vessel that belong to a specific **reportType** (e.g., \"NEAR MISS REPORT\", \"ACCIDENT / INCIDENT REPORT\"). You can also, if needed, narrow the results to a particular **stage** (OPEN, OPEN OVERDUE, or CLOSED).\n\nHow to use it\n1. Identify the vessel by its IMO number (or name).\n2. Select one of the allowed **reportType** enum values.\n3. (Optional) Provide a **stage** filter—choose ONE of \"OPEN\", \"OPEN OVERDUE\", or \"CLOSED\". Omit this field if you want all stages.\n4. Query the *defect* collection combining the vessel's `imo`, the chosen `reportType`, and—if supplied—the `stage` value.\n5. Optionally set how many results to return per page.\n\nExample: \"Open Near-Miss reports for VESSEL_NAME\" → use `imo=IMO_NUMBER`, `reportType=\"NEAR MISS REPORT\"`, `stage=OPEN`.",
        inputSchema={
            "type": "object",
            "required": ["imo", "reportType"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "reportType": {
                    "type": "string",
                    "description": "Report type to filter. Multiple types can be sent as comma separated values.",
                    "enum": [
                        "ACCIDENT / INCIDENT REPORT",
                        "BEST PRACTICE",
                        "COC",
                        "DEFICIENCY",
                        "DEVIATION",
                        "DISPENSATION",
                        "FAILURE",
                        "HULL MACHINERY DEFECT/HMX",
                        "LARP",
                        "MEMO/MEMORANDA",
                        "NC/NON CONFORMITY REPORT",
                        "NEAR MISS REPORT",
                        "NOTES",
                        "OBSERVATION",
                        "SUGGESTION FOR IMPROVEMENTS",
                        "SUSPENSION",
                        "SHIPBOARD MANAGEMENT REVIEW",
                        "RISK MANAGEMENT",
                        "VESSEL REJECTION",
                        "MANAGEMENT OF CHANGE/MGMT OF CHANGE",
                        "SAFETY MEETING"
                    ]
                },
                "stage": {
                    "type": "string",
                    "enum": ["OPEN", "OPEN OVERDUE", "CLOSED"],
                    "description": "Optional stage filter (omit to include all stages)."
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
        name="list_defects_by_status",
        description="Use this tool to list defect / safety-management records for a vessel that match one or more **currentStatus** values (e.g., \"READY OFFICE REVIEW\", \"OPEN\", \"CLOSED\"). You may also, if required, narrow the results further with a **stage** filter (OPEN, OPEN OVERDUE, or CLOSED).\n\nHow to use it\n1. Identify the vessel by its IMO number (or name).\n2. Select one or more **currentStatus** values from the enum values.\n3. (Optional) Provide a **stage** filter (\"OPEN\", \"OPEN OVERDUE\", or \"CLOSED\") if the user specifies one; otherwise omit it.\n4. Query the *defect* collection combining the vessel's `imo`, the chosen `currentStatus` value(s), and—if supplied—the `stage` value.\n5. Optionally set how many results you want per page.\n\nExample question: \"List defects which are **READY OFFICE REVIEW** for VESSEL_NAME.\" → use `imo = IMO_NUMBER`, `currentStatus = READY OFFICE REVIEW`.",
        inputSchema={
            "type": "object",
            "required": ["imo", "currentStatus"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "currentStatus": {
                    "type": "string",
                    "description": "Defect status to filter.",
                    "enum": [
                        "AMENDED",
                        "APPROVED",
                        "ACCEPTED",
                        "CLOSED",
                        "CLOSURE VERIFICATION",
                        "DRAFT",
                        "OFFICE REVIEW IN PROGRESS",
                        "INVESTIGATION COMPLETED",
                        "IN PROGRESS",
                        "OPEN",
                        "PIC REVIEW IN PROGRESS",
                        "PENDING APPROVAL",
                        "RE-OPENED",
                        "READY OFFICE REVIEW",
                        "READY SHIP REVIEW",
                        "REGENERATE REPORT TYPE",
                        "REQUEST SUBMITTED SHORE",
                        "REQUEST SUBMITTED VESSEL",
                        "RETURNED",
                        "REQUESTED",
                        "REVIEW IN PROGRESS SHIP",
                        "REVIEW IN PROGRESS SHORE",
                        "REVIEW IN PROGRESS",
                        "SHIP REVIEW RETURNED",
                        "SEND BACK TO VESSEL",
                        "UNDER AMENDMENT",
                        "VERIFIED"
                    ]
                },
                "stage": {
                    "type": "string",
                    "enum": ["OPEN", "OPEN OVERDUE", "CLOSED"],
                    "description": "Optional stage filter (omit to include all stages)."
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
    )
]



# MongoDB tool definitions for mcp_pms

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
      types.Tool(
        name="get_defect_table_schema",
        description="This tool retrieves Typesense defect table schema and instructions on how to query the defect table for a specific category.",
        inputSchema={
            "type": "object",
            "required": ["category"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category for which to retrieve the Typesense schema.",
                    "enum": ["defect"]
                }
            }            
        }
    ),
    types.Tool(
        name="get_tmsa_summary",
        description="This tool gives the recent TMSA checklist for the vessel, including date and time, in a downloadable format.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="get_sire_reports_from_ocimf",
        description="Use this tool to get SIRE inspection status, days remaining, last inspection date, company, and report status of the vessel from OCIMF website. The reports are also available to download. It also provides recent SIRE inspection details, including date, company, location, vessel status, and validity.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="fetch_fleet_historical_sire_observations",
        description="Use this tool to get the fleet's historical SIRE observations from OCIMF website. Example Question: Get me the SIRE observations received by the fleet",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_cdi_reports_from_ocimf",
        description="Use this tool to get last CDI inspection date, company, validity, days until next inspection, observations, report link, and questionnaires",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="get_vir_status_overview",
        description="Use this tool to get data from the VIR app and ShipPalm Defect module. It shows the next VIR due date, type (Port or Sailing), and a countdown of days remaining or overdue. It also includes details of the last VIR—date, type, number of defects raised, and their current status (Open/Closed/Overdue).",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="get_internal_audit_summary",
        description="use this tool to get summary of last Internal Audit which includes ISM, ISPS and Dynamic Navigational Audit , the dates when done and the defects. Also provides details to plan the next audit, like due date, number of days remaining etc.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="get_psc_inspection_defects",
        description="use this tool to get last PSC inspection details and also historical record of PSC inspection dates.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
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
        name="get_summary_of_defects",
        description="Use this tool to get list of defects from various sources like Ship Palm defect module, Class Websites, OCIMF Website, Various MOU websites are checked and a summary is prepared showing how many Overdue or coming due soon.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "additionalProperties": False
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


# Document Parser Tools
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
                    "enum": ["Internal Audit", "Sire", "VIR"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["internalAudit", "sire", "vir"],
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
                    "enum": ["internalAudit", "sire", "vir"],  #internalAudit sire vir
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
tool_definitions = typesense_tools + mongodb_tools + document_parser_tools + general_tools  + casefile_tools
