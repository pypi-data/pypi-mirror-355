from mcp_pms.databases import *
import mcp.types as types

# Typesense tool definitions for mcp_pms

typesense_tools = [
    # types.Tool(
    #     name="pms_lubereport_table_query",
    #     description="[FALLBACK TOOL] Search the PMS or lube oil reports collection in typesense.It is mandatory to get the schema of the collection first using **get_table_schema** tool, then use the schema to search the required collection.  Use this tool when other more specialized tools have failed to provide sufficient information or when you want to search the certificate collection for a specific keyword or when more data is needed for any trend analysis that needs to be done. This is a generic search tool with less targeted results than purpose-built tools. Example questions : 1. Give me the name of testLab used for oil analysis for < vessel>",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search",
    #                 "enum": ["pms"]
    #             },
    #             "query": {
    #                 "type": "object",
    #                 "description": "Query parameters for the search"
    #             }
    #         },
    #         "required": ["collection", "query"]
    #     }
    # ),
    types.Tool(
        name="lube_report_table_query",
        description="[FALLBACK TOOL] Searches planned maintenance system (PMS jobs, schedules, overhauls, components) and lube oil analysis reports (test labs, sample dates, machinery analysis status) databases. Use when other PMS/lube oil tools fail or for keyword searches across multiple fields. Always get the schema first using get_lube_report_table_schema tool. Example: Find test lab used for main engine oil analysis on <vessel>",
        inputSchema={
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "Name of the collection to search",
                    "enum": ["lube_oil_reports"]
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
            "required": ["collection", "query"],
            "additionalProperties": False
        }
    ),
    # types.Tool(
    # name="get_fuel_oil_analysis_table_schema",
    # description="This tool retrieves Typesense schema for fuel_oil_data collection and instructions on how to query the fuel oil data table for a specific category.",
    # inputSchema={
    #     "type": "object",
    #     "required": ["category"],
    #     "properties": {
    #         "category": {
    #             "type": "string",
    #             "description": "The category for which to retrieve the Typesense schema (e.g., fuel_oil_data, bunker_analysis).",
    #             "enum": ["fuel_oil_data"]
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    # types.Tool(
    # name="fuel_oil_analysis_table_query", 
    # description="[FALLBACK TOOL] Search the fuel oil analysis collection in typesense. It is mandatory to get the schema of the collection first using **get_fuel_oil_analysis_table_schema** tool, then use the schema to search the required collection. Use this tool when other more specialized tools have failed to provide sufficient information or when you want to search the fuel oil analysis collection for a specific keyword or when more data is needed for any trend analysis that needs to be done. This is a generic search tool with less targeted results than purpose-built tools. Example questions: 1. Give me the storage temperature for the latest VLSFO bunker taken for <vessel> ",
    # inputSchema={
    #     "type": "object",
    #     "properties": {
    #         "collection": {
    #             "type": "string",
    #             "description": "Name of the collection to search",
    #             "enum": ["fuel_oil_data"]
    #         },
    #         "query": {
    #             "type": "object",
    #             "description": "Query object to send to Typesense's search endpoint.",
    #             "properties": {
    #                 "q": {
    #                     "type": "string",
    #                     "description": "Search string. Use '*' to match all records."
    #                 },
    #                 "query_by": {
    #                     "type": "string",
    #                     "description": "Comma-separated list of fields to apply the `q` search on. Example: 'field1,field2'."
    #                 },
    #                 "filter_by": {
    #                     "type": "string",
    #                     "description": "Filter expression using Typesense syntax. Use ':' for equality, '<'/'>' for ranges. Combine multiple conditions using '&&' or '||'. Example: 'imo:<imo_number> && type:<certificate_type> && daysToExpiry:<cutoff_timestamp>'"
    #                 },
    #                 "include_fields": {
    #                     "type": "string",
    #                     "description": "Comma-separated list of fields to include in the results. Example: 'field1,field2,field3'."
    #                 },
    #                 "per_page": {
    #                     "type": "number",
    #                     "description": "Number of results to return per page, defaults to 10"
    #                 }
    #             },
    #             "required": ["q", "query_by"],
    #             "additionalProperties": False
    #         }
    #     },
    #     "required": ["collection", "query"],
    #     "additionalProperties": False
    #     }
    # ),
    types.Tool(
        name="list_pms_jobs_by_category_and_status",
        description="Use this tool to list Planned-Maintenance (PMS) jobs for a vessel that match a specific **job category** and **job status**.\n\nHow it works:\n1. Identify the vessel by IMO (or name).\n2. Choose the desired **jobCategory** – either \"CRITICAL\" or \"NON-CRITICAL\" (these are fixed enum values).\n3. Choose the desired **jobStatus** – for example \"OVERDUE\", \"IN ORDER\" (these are fixed enum values).  The value must exactly match what is stored in the database.\n4. Query the *pms* collection combining all three filters: `imo`, `jobCategory`, and `jobStatus`.\n5. Optionally specify how many results you want per page.\n\nExample question: \"Fetch the list of NON-CRITICAL PMS jobs that are OVERDUE for VESSEL_NAME.\"",
        inputSchema={
            "type": "object",
            "required": ["imo", "jobCategory", "jobStatus"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                },
                "jobCategory": {
                    "type": "string",
                    "enum": ["CRITICAL", "NON-CRITICAL"],
                    "description": "Maintenance job category to filter."
                },
                "jobStatus": {
                    "type": "string",
                    "enum": ["OVERDUE", "IN ORDER"],
                    "description": "Status of the job to filter. Value must match the database exactly."
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
        name="list_pms_jobs_for_component",
        description="Use this tool to list Planned-Maintenance (PMS) jobs for a component or machinery (e.g., \"Breathing Air Compressor\").\n\nHow it works:\n1. Identify the vessel by its IMO number (or name).\n2. Provide the component or machinery name you want to match in the PMS **component** field. The match is case-insensitive and may be a full title or a distinctive phrase.\n3. The query combines the vessel's `imo` filter with `component:[<your text>]` and, by default, sorts the results by the next due date (`jobDueDate:asc`) so the most urgent jobs appear first.\n4. Optionally specify how many results to return per page.\n\nExample question: \"Fetch all PMS jobs for the Breathing Air Compressor on BW Pavilion Aranda.\"",
        inputSchema={
            "type": "object",
            "required": ["imo", "component"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel"
                },
                "component": {
                    "type": "string",
                    "description": "Full or partial text to match the component or machinery name(e.g., breathing air compressor)."
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
    # types.Tool(
    #     name="get_maintenance_emails",
    #     description="Use this tool to fetch all vessel-related emails that are tagged as 'maintenance' and were sent within a recent time window:\n1. Take the current date-and-time (UTC).\n2. Subtract the desired look-back period (X hours or days) and get calculated_date_time.\n3. Query the collection for messages whose dateTime is greater than the calculated_date_time **and** whose tags include 'maintenance'.\nProvide the vessel's IMO (or name) and the Date and time from step 2; optionally set how many results you want per page. Example Question: Give me list of maintenance related emails in last 24 hours",
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
    #                 "enum": ["maintenance"]
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
    #     name="get_dailyworkdonereport_emails",
    #     description="Returns vessel-related email messages that are tagged as 'dailyWorkdoneReport' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'dailyWorkdoneReport' covers all emails related to daily work done reports",
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
    #                 "enum": ["dailyWorkdoneReport"]
    #             },
    #             "per_page": {
    #                 "type": "number",
    #                 "description": "Number of emails to return per page (default is 50)."
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),types.Tool(
    #     name="get_report_emails",
    #     description="Returns vessel-related email messages that are tagged as 'report' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'report' covers all emails related to reports",
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
    #                 "enum": ["report"]
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
    #     name="get_maintenance_casefiles",
    #     description="Use this tool to fetch all vessel-related case files that mention the word \"maintenance\", \"pms\" and were sent within a recent time window:\n1. Take the current date-and-time (UTC).\n2. Subtract the desired look-back period (X hours or days) and get calculated_date_time.\n3. Query the caseFiles collection for case files whose lastCasefileUpdateDate is greater than the calculated_date_time **and** casefile field contains the keyword.\nProvide the vessel's IMO (or name) and the Date and time from step 2; optionally set how many results you want per page. Example Question: Give me list of maintenance related case files in last 24 hours",
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
    #                 "description": "The keyword to be searched in the case files (e.g., maintenance, pms)."
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
        name="list_pms_jobs_for_component_due_within",
        description="Use this tool to list Planned-Maintenance (PMS) jobs for a vessel **whose due-date falls within the next *X* days** and that belong to a specific machinery *component* (for example \"purifier\", \"main engine\", or \"steering gear\").\n\nHow to use it\n1. Read the vessel's IMO (or name) and the component keyword from the user's request.\n2. Take the current date-and-time and add the number of days \"X\" as per the user query and get the calculated_date_time.\n3. Query the **pms** collection with three filters combined:\n   • `imo` equal to the vessel's IMO,\n   • `component` equal to the component keyword (case-insensitive substring match), and\n   • `jobDueDate` **less than** the calculated_date_time(`jobDueDate:<calculated_date_time`).\n4. Sort results by `jobDueDate:asc` so the most urgent jobs appear first.\n5. Optionally let the caller set how many results to show per page.\n\nExample question: \"Fetch all purifier PMS jobs that fall due in the next 45 days for VESSEL_NAME\"",
        inputSchema={
            "type": "object",
            "required": ["imo", "component", "days"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "component": {
                    "type": "string",
                    "description": "Machinery component (keyword) to match in the PMS record, e.g., \"purifier\"."
                },
                "days": {
                    "type": "number",
                    "description": "Number of days to look ahead for due dates."
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
    # types.Tool(
    #     name="get_LO_FO_report_emails",
    #     description="Returns vessel-related email messages that are tagged as 'LOandFOReport' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'LOandFOReport' covers all emails related to Lube oil and Fuel oil reports",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo", "tag", "lookbackHours"],
    #        "properties": {
    #            "imo": {
    #                "type": "string",
    #                "description": "The IMO number or name of the vessel"
    #            },
    #            "tag": {
    #                "type": "string",
    #                "description": "The tag to be searched in the emails",
    #                "enum": ["LOandFOReport"]
    #            },
    #            "lookbackHours": {
    #                "type": "integer",
    #                "description": "Rolling window size in hours (e.g., 24 = last day).Optional - Only if a specific window period is provided by the user"
    #            },
    #            "per_page": {
    #                "type": "number",
    #                "description": "Number of requisitions to return per page (default is 250)"
    #            },
    #            "session_id": {
    #                "type": "string",
    #                "description": "Session ID for tracking client sessions, if available"
    #            }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
    types.Tool(
        name="list_overdue_lube_oil_samples",
        description="Retrieve lube-oil analysis records whose next sample is **OVERDUE** for a vessel.\n\nAlways filters on `dueStatus=\"OVERDUE\"` plus the vessel's `imo`.  You may also limit results to a single machinery name.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel."},
                "machineryName": {"type": "string", "description": "Optional machinery name filter."},
                "per_page": {"type": "number", "description": "Records per page (default 30)."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="machinery_with_warning_lube_oil_analysis",
        description="Return all lube oil analysis reports for a vessel where `reportStatus` is **\"WARNING\"** (i.e., unsatisfactory results).  Optional filtering by machinery name is supported.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel."},
                "machineryName": {"type": "string", "description": "Optional machinery name filter."},
                "per_page": {"type": "number", "description": "Records per page (default 30)."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_latest_lube_oil_analysis_for_machinery",
        description="Fetch the most recent lube-oil analysis record for a specific machinery item on a vessel.\n\nSupply `imo` and `machineryName`; the tool sorts by `sampleDate:desc` and returns the first record.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel."},
                "machineryName": {"type": "string", "description": "Machinery name, e.g., \"MAIN ENGINE\"."},
                "per_page": {"type": "number", "description": "Set to 10 (default) because only the newest record is required."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo", "machineryName"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_lube_oil_samples_by_frequency",
        description="Return lube-oil analysis records for a vessel with a specific sampling `frequency` (e.g., \"6 Months\", \"3 Months\").  Results are sorted by `nextDue:asc` so soonest samples appear first.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel."},
                "frequency": {"type": "string", "description": "Sampling frequency to filter, e.g., \"6 Months\"."},
                "per_page": {"type": "number", "description": "Records per page (default 30)."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo", "frequency"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="fetch_lube_oil_analysis_with_link",
        description="This tool retrieves the latest lube oil (LO) analysis report for a specified vessel using its IMO number and for a machinery if name is provided. It fetches the document via a URL, parses the contents, and returns both the parsed LO analysis data and the link to the report.\n\nHow to use it\n1. Provide the vessel's **name** (required).    \n2. (Optional) Provide a specific `machineryName` if you only want the latest report for one item (e.g., \"MAIN ENGINE\").  If you omit `machineryName`, the tool returns the newest report across *all* machinery.  \n3. The tool filters on `vesselName=[name]` and, when supplied, `machineryName=[machinery]`, then sorts by `sampleDate:desc` and returns the document link and the parsed information.",
        inputSchema={
            "type": "object",
            "properties": {
                "vesselName": {"type": "string", "description": "Name of the vessel (case-insensitive match on the vesselName field)."},
                "machineryName": {"type": "string", "description": "Optional machinery name filter (e.g., \"MAIN ENGINE\")."},
                "per_page": {"type": "number", "description": "Set to 10 (default) because only the newest report is needed."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["vesselName"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_overdue_pms_jobs",
        description="Return Planned-Maintenance (PMS) jobs for a vessel that are **OVERDUE**.  \n\nHow to use it\n1. Provide the vessel's IMO number.\n2. (Optional) Supply a `jobCategory` value of **\"CRITICAL\"** or **\"NON-CRITICAL\"** if the user wants to filter by job importance; omit the field to fetch overdue jobs of *all* categories.\n3. The tool filters the PMS collection with:  \n   • `imo = [imo]`  \n   • `jobStatus = \"OVERDUE\"`  \n   • `jobCategory = [jobCategory]` (if provided) ",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "jobCategory": {
                    "type": "string",
                    "enum": ["CRITICAL", "NON-CRITICAL"],
                    "description": "Optional filter to restrict the results to critical or non-critical jobs."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to return per page (default 50)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_latest_fuel_analysis_report",
        description="This tool retrieves the latest fuel oil analysis report for a specified vessel using its vessel name or IMO number and for a specific fuel type if provided. It fetches the document via a URL, parses the contents, and returns both the parsed fuel analysis data and the link to the report.\n\nHow to use it\n1. Provide the vessel's **name** or **IMO number** (required).    \n2. (Optional) Provide a specific `fuelType` if you only want the latest report for one fuel grade (e.g., \"VLSFO\", \"HSFO\", \"MGO\",\"LSMGO\").  If you omit `fuelType`, the tool returns the newest report across *all* fuel types.  \n3. The tool filters on `vesselName=[name]` or `imo=[imo_number]` and, when supplied, `fuelType=[fuel_type]`, then sorts by `bunkerDate:desc` and returns the document link and the parsed fuel analysis information including sulfur content, density, viscosity, compliance comments, and quality ratings.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "number", "description": "IMO number of the vessel"},
                "fuelType": {"type": "string", "description": "Optional fuel type filter (e.g., \"VLSFO\", \"HSFO\", \"MGO\", \"LSMGO\")."},
                "per_page": {"type": "number", "description": "Set to 5 (default) because only the newest report is needed."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_historical_fuel_analysis_data",
        description="This tool retrieves historical fuel oil analysis data for a specified vessel over the last X months or years for trend analysis purposes. It fetches multiple analysis reports within the specified time period, allowing users to analyze fuel quality trends, supplier performance, compliance patterns, and parameter variations over time.\n\nHow to use it\n1. Provide the vessel's **IMO number** (required).\n2. Specify the **lookback period** in months or years (required) - e.g., 6 months, 2 years. The tool will convert years to months internally (1 year = 12 months).\n3. (Optional) Provide a specific `fuelType` to filter results (e.g., \"VLSFO\", \"HSFO\", \"MGO\",\"ULSFO\"). If omitted, returns data for all fuel types.\n4. The tool filters on `imo=[imo_number]`, applies date range filter based on `bunkerDate` for the specified period, and optionally filters by `fuelType`. Results are sorted by `bunkerDate:desc` to show chronological trends.\n5. Returns comprehensive historical data including test dates, fuel parameters, supplier information, compliance trends, and quality ratings for trend analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel."},
                "lookback_months": {"type": "number", "description": "Number of months to look back for historical data (e.g., 6 for last 6 months, 24 for last 2 years)."},
                "fuelType": {"type": "string", "description": "Optional fuel type filter (e.g., \"VLSFO\", \"HSFO\", \"MGO\", \"LSMGO\"). Omit to include all fuel types."},
                "per_page": {"type": "number", "description": "Number of records to return per page (default 100 for comprehensive trend analysis)."},
                "session_id": {"type": "string", "description": "Session ID for tracking client sessions, if available"}
            },
            "required": ["imo", "lookback_months"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="smart_fuel_oil_table_search",
        description=(
            "Universal search tool for vessel fuel oil analysis data and bunker records. "
            "Primary tool for querying fuel analysis reports, bunker delivery notes, fuel quality assessments, and supplier performance across the fleet. "
            "Handles everything from specific fuel sample lookups to fuel quality trends and compliance monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language or keyword query. This is matched against the fields vesselName, bunkerPort, fuelType, "
                        "supplier, testLab, rating, samplingMethod, samplingPoint, barge, and complianceComments. "
                        "Use '*' to match all records."
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
                        "vesselName": {
                            "type": "string",
                            "description": "Exact or partial name of the vessel"
                        },
                        "sampleId": {
                            "type": "string",
                            "description": "Unique sample identification number for the fuel test"
                        },
                        "fuelType": {
                            "type": "string",
                            "description": "Type of fuel (e.g., VLSFO, HSFO, MGO, MDO, LSMGO, ULSFO)"
                        },
                        "supplier": {
                            "type": "string",
                            "description": "Fuel supplier name"
                        },
                        "testLab": {
                            "type": "string",
                            "description": "Laboratory that conducted the fuel analysis"
                        },
                        "rating": {
                            "type": "string",
                            "description": "Overall fuel quality rating (e.g., Normal, Warning, Alert)"
                        },
                        "bunkerPort": {
                            "type": "string",
                            "description": "Port where the fuel was bunkered"
                        },
                        "samplingMethod": {
                            "type": "string",
                            "description": "Method used for fuel sampling"
                        },
                        "samplingPoint": {
                            "type": "string",
                            "description": "Location where fuel sample was taken"
                        },
                        "barge": {
                            "type": "string",
                            "description": "Name of the barge used for fuel delivery"
                        },
                        "bdnReceiptNumber": {
                            "type": "string",
                            "description": "Bunker Delivery Note receipt number"
                        },
                        "bunkerDate_range": {
                            "type": "object",
                            "description": "Filter by bunker date range",
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
                        "sulfur_range": {
                            "type": "object",
                            "description": "Filter by sulfur content percentage",
                            "properties": {
                                "min_sulfur": {
                                    "type": "number",
                                    "description": "Minimum sulfur content percentage"
                                },
                                "max_sulfur": {
                                    "type": "number",
                                    "description": "Maximum sulfur content percentage"
                                }
                            }
                        },
                        "density_range": {
                            "type": "object",
                            "description": "Filter by fuel density at 15°C in kg/m³",
                            "properties": {
                                "min_density": {
                                    "type": "number",
                                    "description": "Minimum density at 15°C"
                                },
                                "max_density": {
                                    "type": "number",
                                    "description": "Maximum density at 15°C"
                                }
                            }
                        },
        
                    }
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                    "enum": ["relevance", "bunkerDate", "sulfur"],
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
        name="get_lube_report_table_schema",
        description="This tool retrieves Typesense schema and instructions on how to query a typesense table for a specific category.",
        inputSchema={
            "type": "object",
            "required": ["category"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category for which to retrieve the Typesense schema (e.g., purchase, voyage, certificates).",
                    "enum": ["lube_oil_reports"]
                }
            }            
        }
    ),
    types.Tool(
        name="get_overall_maintenance_summary",
        description="Use this tool to get focused review of weekly Planned Maintenance System (PMS) items requiring attention, covering a range of metrics including PMS critical and non-critical jobs exceeding set time or hours, deferred jobs, critical spares below minimum levels, and synchronization dates for PMS and noon reports. It also tracks machinery counters not updated in over 15 days, expired vessel certificates as per ship Palm, and open Hull and Machinery (HMX) defects yet to be reviewed. All information is taken from ERP system ShipPalm.",
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
        name="get_main_engine_maintenance_summary",
        description="Use this tool to get a comprehensive overview of Main engine (ME) maintenance status, including the status of ME Units decarbonization (Decarb), ME Units Exhaust valve overhaul, ME Units Fuel valves overhaul, ME Turbocharger Overhaul, ME Units starting air valves overhaul, ME Units Indicator valves Overhaul, ME Units Fuel valves (Fuel Injectors) Overhaul, ME Units Fuel Pumps Overhaul, ME Units Fuel pump suction valves Overhaul etc. It lists the overhaul intervals, current operating hours and the jobs which will be due in future",
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
        name="get_auxiliary_engine_maintenance_summary",
        description="USe this tool to get a comprehensive overview of all auxiliary engines (AE) maintenance status, including the status of decarbonization, connecting rod bolt renewal, cylinder head overhaul, fuel valve overhaul, fuel pump overhaul, governor service, air starting motor service, and turbocharger overhaul. It lists the overhaul intervals, current operating hours and the jobs which will be due in future",
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
        name="get_purifier_maintenance_summary",
        description="Use this tool to get a comprehensive overview of Purifiers (Px) maintenance status. The purifier types can be HFO (Heavy fuel Oil), ME LO (Main Engine Lube Oil), AE LO (Aux Engine Lube Oil), DO (Diesel Oil) etc. The Overview includes the status of purifiers (Px) Top Overhaul, annual routine, 2 yearly routine, 3 yearly routine, Major Overhaul etc. It lists the overhaul intervals, current operating hours and the jobs which will be due in future",
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
        name="get_compressor_maintenance_summary",
        description="Use this tool to get an overview of the Overhaul / maintenance status for all Air compressors, including key jobs like the 250 -hour,1000-hour, 2000-hour, 3000-hour, 6000-hour and Major Overhaul/maintenance routines. It specifies the overhaul intervals, current operating hours and the jobs which will be due in future",
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
        name="get_critical_spares_list",
        description="use this tool to get the list of Critical spares for the vessel with details of each spare like required numbers, present ROB etc.",
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
        name="get_latest_fuel_bunker_details",
        description="Use this tool to get details of the last Bunker (All Grades which were bunkered). The information consists of BDN data like Bunker Date, port, BDN Sulphur, BDN Viscosity, Fuel Grade etc. along with the compliance comments from the testing lab are displayed.",
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
        name="get_lube_oil_shore_analysis",
        description="use this tool to get the details of when the last lube oil samples were landed and what is the status of those samples as per that report. Also, provides when is the next sample landing due with status like in order, due in x days, Overdue etc.",
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
        name="get_month_end_form_submission_status",
        description="Use this tool to get the vessel's month end form submission status . Status means which forms have been completed and submitted.Example Question: Get me form submission status for <vessel>",
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
        name="get_main_engine_performance_review",
        description="Use this tool to get the vessel's main engine performance report and analysis . .Example Question: Fetch main engine performance report and analysis for <vessel>",
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
        name="get_main_engine_scavenge_inspection_review",
        description="Use this tool to get the vessel's main engine scavenge inspection report and analysis . .Example Question: Fetch main engine scavenge inspection report and analysis for <vessel>",
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
        name="get_auxiliary_engine_performance_review",
        description="Use this tool to get the vessel's auxiliary engine performance report and analysis . .Example Question: Fetch auxiliary engine performance report and analysis for <vessel>",
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
        name="get_month_end_consolidated_technical_report",
        description="Use this tool to get the vessel's month end consolidated technical report .Consolidated technical report is generated from all the month end technical forms which the vessel submits..Example Question: Get me month end technical report for <vessel>",
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
        name="get_latest_engine_performance",
        description="Retrieve the latest engine (MAIN ENGINE - ME , AUXILIARY ENGINE - AE) performance data for a specific vessel. **How to invoke** 1. Provide the vessel's `imo` number (required). 2. Optionally specify `ENGINENAME` to get data for a specific engine only. If `ENGINENAME` is omitted, returns latest performance data for all engines on the vessel. 3. The tool returns the most recent performance record(s) including engine load, temperatures, pressures, fuel consumption, alerts, and all key performance indicators.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "number",
                    "description": "IMO number of the target vessel."
                },
                "ENGINENAME": {
                    "type": "string",
                    "enum": [
                        "AE1",
                        "AE2", 
                        "AE3",
                        "AE4",
                        "AE5",
                        "ME"
                    ],
                    "description": "Optional. Specific engine name to filter results. If not provided, returns latest data for all engines. User can use short forms like ME or M/E for Main Engine . For Auxillary Engine user can query with A/E , AE , DG, D/G , Generator . Understand the user query and apply the appropriate ENUM value"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "required": ["imo"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_historical_engine_performance",
        description="Retrieve historical engine (MAIN ENGINE - ME , AUXILIARY ENGINE - AE) performance data for a specific vessel and engine over a defined time period. **How to invoke** 1. Provide the vessel's `imo` number (required). 2. Specify the `ENGINENAME` for the target engine (required). 3. Define the time period using `startDate` and `endDate` in YYYY-MM-DD format. 4. Optionally set `limit` to control the number of records returned (default = 12, max = 50). The tool returns chronological performance data including trends, alerts, and parameter variations over the specified period.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "number",
                    "description": "IMO number of the target vessel."
                },
                "ENGINENAME": {
                    "type": "string",
                    "enum": [
                        "AE1",
                        "AE2",
                        "AE3", 
                        "AE4",
                        "AE5",
                        "ME"
                    ],
                    "description": "Specific engine name to retrieve historical data for.User can use short forms like ME or M/E for Main Engine . For Auxillary Engine user can query with A/E , AE , DG, D/G , Generator . Understand the user query and apply the appropriate ENUM value"
                },
                "startDate": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date for the historical period in YYYY-MM-DD format."
                },
                "endDate": {
                    "type": "string", 
                    "format": "date",
                    "description": "End date for the historical period in YYYY-MM-DD format."
                },
                "limit": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 12,
                    "description": "Maximum number of performance records to return."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
            },
            "required": ["imo", "ENGINENAME", "startDate", "endDate"],
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
                    "enum": ["LO Analysis Report", "FO Analysis Report"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["loReport","foReport"],
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
                        "Required for 'write_page'. Summary of the new page."
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
    #  types.Tool(
    #     name="retrieve_casefile_data",
    #     description=(
    #         "Retrieves data from casefiles. "
    #         "Supports the following operations:\n"
    #         "- get_casefiles: List all casefiles for a vessel matching a text query.\n"
    #         "- get_casefile_plan: Retrieve the latest plan associated with a specific casefile.\n"
    #         "Only pass arguments explicitly required or allowed for the chosen operation."
    #     ),
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "operation": {
    #                 "type": "string",
    #                 "enum": ["get_casefiles","get_casefile_plan"],
    #                 "description": "Specifies the retrieval operation."
    #             },
    #             "imo": {
    #                 "type": "integer",
    #                 "description": (
    #                     "Required for 'get_casefiles'. IMO number of the vessel."
    #                 )
    #             },
    #             "casefile_url": {
    #             "type": "string",
    #             "description": "The unique identifier of the casefile,  direct casefile url link. Required for operation get_casefile_plan."
    #             },
    #             "query": {
    #                 "type": "string",
    #                 "description": (
    #                     "Optional for 'get_casefiles'. search query to filter casefiles based on the context and user query."
    #                 )
    #             },
    #             "min_importance": {
    #                 "type": "number",
    #                 "minimum": 0,
    #                 "maximum": 100,
    #                 "description": (
    #                     "Optional for 'get_casefiles'. Filter results with importance score ≥ this value."
    #                 )
    #             },
    #             "category": {
    #                 "type": "string",
    #                 "enum": ["loReport","foReport"],
    #                 "description": (
    #                     "Required for 'get_casefiles'. Category of the casefile."
    #                 )
    #             },
    #             "pagination": {
    #                 "type": "integer",
    #                 "default": 1,
    #                 "description": (
    #                     "optional for 'get_casefiles'. Page number for paginated results."

    #                 )
    #             },
    #             "page_size": {
    #                 "type": "integer",
    #                 "default": 10,
    #                 "description": (
    #                     "Optional for 'get_casefiles'. Number of results per page."
    #                 )
    #             }
    #         },
    #         "required": ["operation","imo","category"]
    #     }
    # )


]
# Combined tools for compatibility
tool_definitions = typesense_tools + mongodb_tools + document_parser_tools + general_tools +casefile_tools
