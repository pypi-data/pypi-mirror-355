from .databases import *
import mcp.types as types



# Tool definitions for vessel-related tools
vessel_tools = [
    types.Tool(
        name="get_vessel_live_position_and_eta",
        description="""Use this tool to obtain a vessel's **current live position** (latitude / longitude) and its **estimated time of arrival (ETA)** to the next scheduled port.

    **How to use it:**
    1. Supply the vessel's IMO number (this field is mandatory and uniquely identifies the ship).
    2. The tool calls the real‑time tracking service, fetches the latest AIS/GPS position, identifies the next port of call from the voyage plan, and calculates / returns the ETA.
    3. The response includes at minimum:
      - `latitude`
      - `longitude`
      - `timestamp` (UTC of the position fix)
      - `nextPortName`
      - `etaToNextPort` (ISO date‑time)

    **Example question:**
    "Where is <vessel_name> right now and when will it reach the next port?" → pass its IMO number to this tool.
    Once done, call `get_vessel_eta_from_email` with the same IMO number to get the ETA from emails and send this as *Eta from emails* label.
    """,
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_vessel_fuel_consumption_rob",
        description="Use this tool to retrieve the most recent fuel consumption and Remaining On Board (ROB) data for a specific vessel.\n\nHow to use it:\n1. Supply the vessel's IMO number (mandatory) - this uniquely identifies the ship.\n2. The tool will query the database and return the latest fuel consumption data and ROB information.\n\nThe response includes consumption rates for different fuel types and current quantities remaining on board.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_vessel_eta_cargo_activity",
        description="Use this tool to get the vessel itinerary and cargo activity details from vessel Noon report emails, AIS and Shippalm position report. Specifically, the answer will indicate whether the vessel is sailing, at anchorage/drifting, or in port. For each condition, the next port of call and its Estimated Time of Arrival (ETA) or Estimated Time of Berthing (ETB) or Estimated Time of Departure (ETD) will be provided, if known.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                }
            },
            "required": ["imo"]
        }
    ),

    types.Tool(
        name="get_voyage_details_from_shippalm",
        description=(
            "Use this tool to obtain a vessel's **latest voyage information** from the MongoDB database, where a complete, "
            "pre-computed answer is already stored.\n\n"
            "How to use it:\n"
            "1. Provide the vessel's IMO number — mandatory and uniquely identifies the ship.\n"
            "2. The tool always returns the full structured voyage record.\n\n"
            "Example question: 'What are <vessel_name>'s current voyage details? → pass its IMO number to this tool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),

    types.Tool(
        name="get_me_cylinder_oil_consumption_and_rob",
        description=(
            "Use this tool to fetch a vessel's **most recent main‑engine (ME) cylinder‑lubricating‑oil data** from the MongoDB "
            "database, where a ready‑made answer is already stored.\n\n"
            "How to use it:\n"
            "1. Provide the vessel's IMO number — mandatory and uniquely identifies the ship.\n"
            "2. The tool returns the answer.\n\n"
            "Example question: What is <vessel_name>'s latest ME cylinder‑oil ROB and how much was used in the last 24 hours? → pass its IMO number to this tool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),

    types.Tool(
        name="get_mecc_aecc_consumption_and_rob",
        description=(
            "Use this tool to retrieve a vessel's **most recent main‑engine crankcase (MECC) and auxiliary‑engine crankcase (AECC) "
            "lubricating‑oil data** from the MongoDB database, where a fully prepared answer is already stored.\n\n"
            "How to use it:\n"
            "1. Provide the vessel's IMO number — this is mandatory and uniquely identifies the ship.\n"
            "2. The tool always returns the complete structured answer.\n\n"
            "Example question: What are <vessel_name>'s latest MECC and AECC oil ROBs and daily consumption figures? → pass its "
            "IMO number to this tool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),

    types.Tool(
        name="get_fresh_water_production_consumption_and_rob",
        description=(
            "Use this tool to obtain a vessel's **most recent fresh-water statistics** (production, consumption and remaining-on-board) "
            "from the MongoDB database, where a fully prepared answer is already stored.\n\n"
            "How to use it:\n"
            "1. Supply the vessel's IMO number — this is mandatory and uniquely identifies the ship.\n"
            "2. The tool always returns the complete structured answer.\n\n"
            "Example question: How much fresh water did <vessel_name> make and use yesterday, and what is its current ROB? → pass its "
            "IMO number to this tool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_charter_party_compliance_status",
        description=(
            "Use this tool to retrieve a vessel's **latest charter-party compliance assessment** from the MongoDB database, where a complete, "
            "pre-computed answer is already stored.\n\n"
            "How to use it:\n"
            "1. Provide the vessel's IMO number — mandatory and uniquely identifies the ship.\n"
            "2. The tool always returns the full structured compliance status.\n\n"
            "Example question: Is <vessel_name> currently compliant with its charter-party terms? → pass its IMO number to this tool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_vessel_fuel_consumption_history",
        description="Use this tool to retrieve historical fuel consumption data for a vessel from the MongoDB fuel database . This tool provides comprehensive fuel consumption records including daily consumption for each fuel type Optionally filter by date range for specific time periods to analyse consumption patterns. Use this when you need: fuel consumption analysis and trends, bunker planning and optimization, environmental compliance reporting (like EU MRV, IMO DCS), voyage efficiency analysis, fuel cost analysis over time, or when the user specifically asks for fuel consumption data, bunker history, or fuel efficiency metrics. Example questions: 'Show fuel consumption for VESSEL_NAME last 6 months', 'Get fuel consumption history for VESSEL_NAME since January 2024', 'Analyze fuel efficiency trends for VESSEL_NAME', 'What is the daily fuel consumption for VESSEL_NAME?'",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel"},
                "start_date": {"type": "string", "description": "Optional start date for filtering fuel consumption records (YYYY-MM-DD format). Filter will include consumption data from this date onwards"},
                "end_date": {"type": "string", "description": "Optional end date for filtering fuel consumption records (YYYY-MM-DD format). Filter will include consumption data up to this date"}
            },
            "additionalProperties": False
        }
    ),

    # types.Tool(
    #     name="get_itinerary_emails",
    #     description=(
    #         "Use this tool to retrieve vessel-related email messages that are tagged as 'itinerary' and were sent within the last N hours or                  days for a specified vessel from the `diary_mails` collection in Typesense.\n\n"
    #         "This tag cover all emails related to vessel itinerary (ETA, ETB, ETD, next port details) and cargo activity updates.\n\n"
    #         "How to use it:\n"
    #         "1. Provide the vessel's IMO number or name — mandatory to identify the ship.\n"
    #         "2. Choose the tag to filter emails.\n"
    #         "3. Optionally, provide a lookback window in hours to limit how far back to search.\n\n"
    #         "Example question: 'Show all itinerary and cargo update emails for <vessel_name> in the last 48 hours.'"
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number or name of the vessel."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "The tag to search in the emails. Only 'Itinerary' emails are allowed.",
    #                 "enum": ["itinerary"]
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day). Optional — used if a specific window is provided by the user."
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of results to return per page (default is 10)."
    #             }
    #         },
    #         "required": ["imo", "tag"]
    #     }
    # ),
    # types.Tool(
    #    name="get_agent_details_emails",
    #     description=(
    #         "Use this tool to retrieve vessel-related email messages that are tagged as 'agent' and were sent within the last N hours or                  days for a specified vessel from the `diary_mails` collection in Typesense.\n\n"
    #         "This tag cover all emails related to the shipping agent assigned to the vessel .\n\n"
    #         "How to use it:\n"
    #         "1. Provide the vessel's IMO number or name — mandatory to identify the ship.\n"
    #         "2. Choose the tag to filter emails.\n"
    #         "3. Optionally, provide a lookback window in hours to limit how far back to search.\n\n"
    #         "Example question: 'Show all itinerary and cargo update emails for <vessel_name> in the last 48 hours.'"
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number or name of the vessel."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "The tag to search in the emails. Only 'agent' emails are allowed.",
    #                 "enum": ["agent"]
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day). Optional — used if a specific window is provided by the user."
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of results to return per page (default is 10)."
    #             }
    #         },
    #         "required": ["imo", "tag"]
    #     }
    # ),
    # types.Tool(
    #     name="get_voyage_casefiles",
    #     description=(
    #         "Use this tool to fetch vessel-related case files that mention specific voyage or itinerary keywords such as "
    #         "'Itinerary', 'ETA', 'next port', 'current position', etc., and were updated within a recent time window.\n\n"
    #         "How to use it:\n"
    #         "1. Provide the vessel's IMO number (or name).\n"
    #         "2. Provide a lookback period in hours to define how far back from the current UTC time to search.\n"
    #         "3. Provide the keyword to search in the `casefile` field.\n"
    #         "4. Optionally, specify the number of results to return per page.\n\n"
    #         "Internally, this tool:\n"
    #         "- Calculates the datetime by subtracting `lookback_hours` from the current UTC time.\n"
    #         "- Queries the `caseFiles` collection where `lastCasefileUpdateDate` is greater than the calculated time AND the `casefile` field contains the keyword.\n\n"
    #         "Example question: 'Give me the voyage or itinerary-related casefiles for <vessel_name> from the last 24 hours.'"
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number or name of the vessel."
    #             },
    #             "lookback_hours": {
    #                 "type": "integer",
    #                 "description": "Number of hours to look back from current UTC time."
    #             },
    #             "query_keyword": {
    #                 "type": "string",
    #                 "description": "Keyword to search within the `casefile` field (e.g., 'ETA', 'next port', etc.)."
    #             },
    #             "per_page": {
    #                 "type": "integer",
    #                 "description": "Number of casefiles to return per page (default is 10)."
    #             }
    #         },
    #         "required": ["imo", "lookback_hours", "query_keyword"]
    #     }
    # ),

    # types.Tool(
    #     name="get_laycan_emails",
    #     description=(
    #         "Use this tool to retrieve vessel-related email messages tagged as 'Laycan' from the `diary_mails` collection in Typesense.\n\n"
    #         "The tag 'Laycan' covers emails that mention the laycan period (laydays/cancelling) or any updates related to it.\n\n"
    #         "How to use it:\n"
    #         "1. Provide the vessel's IMO number or name.\n"
    #         "2. Use the fixed tag 'Laycan'.\n"
    #         "3. Optionally, provide a lookback window in hours to filter emails from the recent past.\n"
    #         "4. You can also specify how many results to return per page.\n\n"
    #         "Example question: 'Show all laycan-related emails for <vessel_name> in the last 48 hours.'"
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number or name of the vessel."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "Email classification tag. Only 'Laycan' is supported.",
    #                 "enum": ["Laycan"]
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day). Optional."
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 10)."
    #             }
    #         },
    #         "required": ["imo", "tag"]
    #     }
    # ),

    # types.Tool(
    #     name="get_charterer_emails",
    #     description=(
    #         "Use this tool to retrieve vessel-related email messages tagged as 'charterer' from the `diary_mails` collection in Typesense.\n\n"
    #         "The 'charterer' tag includes emails related to charterers or any voyage instructions issued by the charterer.\n\n"
    #         "How to use it:\n"
    #         "1. Provide the vessel's IMO number or name.\n"
    #         "2. Use the fixed tag 'charterer'.\n"
    #         "3. Optionally, provide a lookback window in hours to filter emails within a recent period.\n"
    #         "4. You may also specify how many results to return per page.\n\n"
    #         "Example question: 'Show me the charter-related emails for <vessel_name> from the last 24 hours.'"
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number or name of the vessel."
    #             },
    #             "tag": {
    #                 "type": "string",
    #                 "description": "Email classification tag. Only 'charterer' is supported.",
    #                 "enum": ["charterer"]
    #             },
    #             "lookbackHours": {
    #                 "type": "integer",
    #                 "description": "Rolling window size in hours (e.g., 24 = last day). Optional."
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 10)."
    #             }
    #         },
    #         "required": ["imo", "tag"]
    #     }
    # )
]

# Tool definitions for weather-related tools
weather_tools = [
    types.Tool(
        name="get_live_weather_by_coordinates",
        description="Use this tool to retrieve the **current (or nearest‑in‑time) weather conditions** at a specific geographic position.\n\n**Required workflow**\n1. Call `get_vessel_live_position_and_eta` with the vessel's IMO number. That tool returns `latitude`, `longitude`, and a `timestamp` (UTC) for the position fix.\n2. Pass all three values—`latitude`, `longitude`, and `timestamp`—to **this** tool. The timestamp ensures the weather data corresponds to the exact moment of the position report.\n3. The response includes, at minimum: `airTemperature`, `windSpeed`, `windDirection`, `pressure`, `humidity`, and `time` (UTC).\n\nExample sequence:\n*Step 1* – `get_vessel_live_position_and_eta` → `{ latitude: 12.3456, longitude: -45.6789, timestamp: \"2025‑05‑07T06:30:00Z\", … }`\n\n*Step 2* – Call this tool with `{ latitude: 12.3456, longitude: -45.6789, timestamp: \"2025‑05‑07T06:30:00Z\" }` to receive the weather conditions for that exact time and location.",
        inputSchema={
            "type": "object",
            "required": ["latitude", "longitude", "timestamp"],
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Latitude extracted from the information given by get_vessel_live_position_and_eta tool"
                },
                "longitude": {
                    "type": "number",
                    "description": "Longitude extracted from the information given by get_vessel_live_position_and_eta tool"
                },
                "timestamp": {
                    "type": "string",
                    "description": "ISO UTC timestamp of the position fix extracted from the information given by get_vessel_live_position_and_eta tool"
                }
            },
            "additionalProperties": False
        }
    )
]

# Tool definitions for search-related tools
search_tools = [
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
        name="get_voyage_table_schema",
        description="This tool retrieves Typesense schema of voyage table and instructions on how to query the voyage table for a specific category.",
        inputSchema={
            "type": "object",
            "required": ["category"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category for which to retrieve the Typesense schema",
                    "enum": ["voyage"]
                }
            }            
        }
    ),
    types.Tool(
        name="voyage_table_search",
        description="[FALLBACK TOOL] Searches ship voyage records database containing daily as well as historical reports with fuel oil, lube oils , fresh water consumption and their ROB, cargo data, locations,ETA, weather, and operational details. Use when other voyage tools do not give sufficient information or for trend analysis across multiple fields. Always get the schema first using the get_voyage_table_schema tool. Example: Find fuel consumption trends for vessel ABC over 6 months",
        inputSchema={
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "Name of the collection to search.",
                    "enum": ["voyage"]
                },
                "query": {
                    "type": "object",
                    "description": "Query object to send to Typesense's search endpoint.",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": "Search string. Use '*' to match all records."
                        },
                        "query_by": {
                            "type": "string",
                            "description": "Comma-separated list of fields to apply the `q` search on. Example: 'field1,field2'."
                        },
                        "filter_by": {
                            "type": "string",
                            "description": "Filter expression using Typesense syntax. Use ':' for equality, '<'/'>' for ranges. Combine multiple conditions using '&&' or '||'. Example: 'imo:<imo_number> && type:<certificate_type> && daysToExpiry:<cutoff_timestamp>'"
                        },
                        "include_fields": {
                            "type": "string",
                            "description": "Comma-separated list of fields to include in the results. Example: 'field1,field2,field3'."
                        },
                        "per_page": {
                            "type": "number",
                            "description": "Number of results to return per page, defaults to 10"
                        }
                    },
                    "required": ["q", "query_by"]
                }
            },
            "required": ["collection", "query"]
        }
    ),
    types.Tool(
        name="smart_voyage_search",
        description=(
            "Universal search tool for vessel voyage data, operational reports, and performance analytics. "
            "Primary tool for querying voyage reports, fuel consumption, cargo operations, and vessel performance across the fleet. "
            "Handles everything from specific voyage lookups to fuel efficiency analysis and operational performance monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language or keyword query. This is matched against the fields vesselName, event, eventtype, "
                        "fromport, toport, location, vesselActivity, vesselstatus, headcharterer, and data fields containing "
                        "cargo, fuel, lube oil, fresh water, and weather information. Use '*' to match all records."
                    ),
                    "default": "*"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
                    "properties": {
                        "imo": {
                            "type": "integer",
                            "description": "IMO number of the vessel"
                        },
                        "vesselName": {
                            "type": "string",
                            "description": "Exact or partial name of the vessel"
                        },
                        "event": {
                            "type": "string",
                            "description": "Operational event onboard (e.g., BUNKERING, ARRIVAL). Use only when the user names a specific event"
                        },
                        "eventtype": {
                            "type": "string",
                            "description": "Report category under which the event is logged (e.g., REPORT, CORRECTION). Use only when user specifies a type"
                        },
                        "fromport": {
                            "type": "string",
                            "description": "Port of departure for current voyage leg"
                        },
                        "toport": {
                            "type": "string",
                            "description": "Destination port for current voyage leg"
                        },
                        "location": {
                            "type": "string",
                            "description": "Current geographical location or position of vessel"
                        },
                        "vesselActivity": {
                            "type": "string",
                            "description": "Current activity status of the vessel (e.g., steaming, at anchor, loading)"
                        },
                        "vesselstatus": {
                            "type": "string",
                            "description": "Current operational status of the vessel"
                        },
                        "atPort": {
                            "type": "string",
                            "description": "Indicates if vessel is currently at port"
                        },
                        "headcharterer": {
                            "type": "string",
                            "description": "Head charterer information"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Time zone of the vessel location during reporting"
                        },
                        "reportdate_range": {
                            "type": "object",
                            "description": "Filter by report date range",
                            "properties": {
                                "start_date": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "Start date-time (YYYY-MM-DDTHH:MM:SS)"
                                },
                                "end_date": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "End date-time (YYYY-MM-DDTHH:MM:SS)"
                                }
                            }
                        },
                        "steamingTime_range": {
                            "type": "object",
                            "description": "Filter by steaming hours during reporting period",
                            "properties": {
                                "min_hours": {
                                    "type": "integer",
                                    "description": "Minimum steaming hours"
                                },
                                "max_hours": {
                                    "type": "integer",
                                    "description": "Maximum steaming hours"
                                }
                            }
                        },
                    }
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                    "enum": ["relevance", "imo", "reportdate", "steamingTime", "steaminghours"],
                    "default": "relevance"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sorting order of the results",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"],
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
mongodb_tool = [
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
                    "enum": ["Charter Party"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["charterParty"],
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
                    "enum": ["charterParty"],
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
tool_definitions = vessel_tools + weather_tools + search_tools + mongodb_tool + document_parser_tools + general_tools + casefile_tools
