from mcp_crew.databases import *
import mcp.types as types

# Typesense tool definitions for mcp_pms

typesense_tools = [
            # types.Tool(
            #     name="get_crew_emails",
            #     description="Returns vessel-related email messages that are tagged as 'crewlist' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'crewlist' covers all emails related to crew list or crew details",
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
            #             "per_page": {
            #                 "type": "number",
            #                 "description": "Number of emails to return per page (default is 5)."
            #             },
            #             "tag": {
            #                 "type": "string",
            #                 "description": "The tag to be searched in the emails",
            #                 "enum": ["crewlist"]
            #             }
            #         },
            #         "additionalProperties": False
            #     }
            # ),
            # types.Tool(
            #     name="get_crew_casefiles",
            #     description="Use this tool to fetch all vessel-related case files that mention the word \"crew\" and were sent within a recent time window:\n1. Take the current date-and-time (UTC).\n2. Subtract the desired look-back period (X hours or days) and get calculated_date_time.\n3. Query the caseFiles collection for case files whose lastCasefileUpdateDate is greater than the calculated_date_time **and** casefile field has the text \"crew\".\nProvide the vessel's IMO (or name) and the Date and time from step 2; optionally set how many results you want per page. Example Question: Give me list of crew related case files in last 24 hours",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["imo", "lookbackHours"],
            #         "properties": {
            #             "imo": {
            #                 "type": "string", 
            #                 "description": "The IMO number of the vessel"
            #             },
            #             "lookbackHours": {
            #                 "type": "integer",
            #                 "description": "Rolling window size in hours (e.g., 24 = last day)."
            #             },
            #             "per_page": {
            #                 "type": "number",
            #                 "description": "Number of case files to return per page (default is 5)."
            #             }
            #         },
            #         "additionalProperties": False
            #     }
            # ), 
            # types.Tool(
            #     name="crew_table_query",
            #     description="[FALLBACK TOOL] Searches crew roster database containing seafarer names, positions/ranks, contract dates, sign-on/off schedules, and vessel assignments. Use when other crew tools do not give sufficient information or for keyword searches across multiple fields. Always get the schema first using the get_crew_table_schema tool. Example: 'Find chief engineer name on <vessel>",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "collection": {
            #                 "type": "string",
            #                 "description": "Name of the collection to search.",
            #                 "enum": ["crew"]
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
            # types.Tool(
            #     name="smart_crew_list_search",
            #     description=(
            #         "Universal search tool for vessel crew records and seafarer information. "
            #         "Primary tool for querying crew data across the fleet including contract details, positions, and assignments. "
            #         "Handles everything from specific crew member lookups to contract expiry tracking and crew roster management."
            #     ),
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "query": {
            #                 "type": "string",
            #                 "description": (
            #                     "Natural language or keyword query. This is matched against the fields Name, POSITION_NAME and CREW_CODE. Use '*' to match all records."
            #                 ),
            #                 "default": "*"
            #             },
            #             "filters": {
            #                 "type": "object",
            #                 "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
            #                 "properties": {
            #                     "imo": {
            #                         "type": "number",
            #                         "description": "IMO number of the vessel"
            #                     },
            #                     "VESSEL_NAME": {
            #                         "type": "string",
            #                         "description": "Exact or partial name of the vessel"
            #                     },
            #                     "Name": {
            #                         "type": "string",
            #                         "description": "Exact or partial name of the seafarer"
            #                     },
            #                     "POSITION_NAME": {
            #                         "type": "string",
            #                         "description": "Current position, rank, or title of the seafarer (e.g., 'Master', 'Chief Engineer', 'Second Engineer')"
            #                     },
            #                     "CREW_CODE": {
            #                         "type": "string",
            #                         "description": "Unique crew code assigned to the seafarer"
            #                     },
            #                     "CONTRACT_END_DATE_range": {
            #                         "type": "object",
            #                         "description": "Filter by contract end date",
            #                         "properties": {
            #                             "start_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "Start date (YYYY-MM-DD)"
            #                             },
            #                             "end_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "End date (YYYY-MM-DD)"
            #                             }
            #                         }
            #                     },
            #                     "SIGN_ON_DATE_range": {
            #                         "type": "object",
            #                         "description": "Filter by date the seafarer signed on to the vessel",
            #                         "properties": {
            #                             "start_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "Start date (YYYY-MM-DD)"
            #                             },
            #                             "end_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "End date (YYYY-MM-DD)"
            #                             }
            #                         }
            #                     },
            #                     "SIGN_OFF_DATE_range": {
            #                         "type": "object",
            #                         "description": "Filter by scheduled sign off date from the vessel",
            #                         "properties": {
            #                             "start_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "Start date (YYYY-MM-DD)"
            #                             },
            #                             "end_date": {
            #                                 "type": "string",
            #                                 "format": "date",
            #                                 "description": "End date (YYYY-MM-DD)"
            #                             }
            #                         }
            #                     }
            #                 }
            #             },
            #             "sort_by": {
            #                 "type": "string",
            #                 "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
            #                 "enum": ["relevance", "CONTRACT_END_DATE", "SIGN_ON_DATE", "SIGN_OFF_DATE"],
            #                 "default": "relevance"
            #             },
            #             "sort_order": {
            #                 "type": "string",
            #                 "description": "Sorting order of the results",
            #                 "enum": ["asc", "desc"],
            #                 "default": "asc"
            #             },
            #             "max_results": {
            #                 "type": "number",
            #                 "description": "Maximum number of results to return",
            #                 "default": 50,
            #                 "minimum": 1,
            #                 "maximum": 100
            #             }
            #         },
            #         "required": ["query"],
            #                     "additionalProperties": False
            #     }
            # ),
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
            #     name="list_crew_contracts_ending_within",
            #     description="Use this tool to list crew members whose onboard contracts will end **within the next N days (or months)** for a specified vessel.\n\nHow it works:\n1. Identify the vessel by its IMO number (or name).\n2. Convert the requested horizon **N** into a date : *cutoff = today + N days* (or the equivalent number of seconds for N months).\n3. Query the **crew** collection with two filters:\n   • `imo` equal to the vessel's IMO, and\n   • `CONTRACT_END_DATE` less than the cutoff_date(`CONTRACT_END_DATE:<cutoff_date`).\n4. Optionally specify how many results to return per page.\n\nExample question: \"Show me all crew members whose contracts end in the next 60 days for VESSEL_NAME.\"",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["imo", "days"],
            #         "properties": {
            #             "imo": {
            #                 "type": "string", 
            #                 "description": "The IMO number of the vessel"
            #             },
            #             "days": {
            #                 "type": "number",
            #                 "description": "Number of days to look ahead for contract end dates."
            #             },
            #             "per_page": {
            #                 "type": "number",
            #                 "description": "Number of crew records to return per page (default is 250)."
            #             },
            #             "session_id": {
            #                 "type": "string",
            #                 "description": "Session ID for tracking client sessions, if available"
            #             }
            #         },
            #         "additionalProperties": False
            #     }
            # ),
            # types.Tool(
            #     name="list_crew_members",
            #     description="Return the **current crew roster** for a vessel. Supply the vessel's IMO number and the tool will query the `crew` collection and return each seafarer's name, rank, sign-on date, contract end date, and other basic details.",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["imo"],
            #         "properties": {
            #             "imo": {
            #                 "type": "string",
            #                 "description": "IMO number of the vessel."
            #             },
            #             "session_id": {
            #                 "type": "string",
            #                 "description": "Session ID for tracking client sessions, if available"
            #             }
            #         },
            #         "additionalProperties": False
            #     }
            # ),
            types.Tool(
                name="get_seafarer_id",
                description="""
                            Get Seafarer IDs(crew code) from user query by querying in typesense crew_details collection. This seafarer id is used to get the seafarer details like name, rank,nationality, contract end date, sign on date, etc. from the snowflake database using the get_seafarer_details tool right after this tool.
                        
                            ## SCHEMA OF THE crew_details TABLE in TYPESENSE.

                            * 'name': 'AGE', 'type': 'string', 'desc': 'Age of the seafarer in years. To be used for querying the seafarers based on age', 'index': true, 'sort': true
                            * 'name': 'CREW_CODE', 'type': 'string', 'desc': 'Primary crew identifier for the seafarer in the crewing system. To be used for querying the seafarers based on crew code', 'index': true, 'sort': false
                            * 'name': 'OLD_CREW_CODE', 'type': 'string', 'desc': 'Legacy crew identifier retained for historical cross-reference. To be used for querying the seafarers based on old crew code', 'index': true, 'sort': false
                            * 'name': 'SEAFARER_NAME', 'type': 'string', 'desc': 'Full name of the seafarer as recorded in official documents. To be used for querying the seafarers based on name', 'index': true, 'sort': false
                            * 'name': 'CURRENT_RANK_NAME', 'type': 'string', 'desc': 'Current rank/position held onboard (e.g., Chief Cook, Master). Note: Captain should be treated as Master while querying the seafarers based on rank', 'index': true, 'sort': false
                            * 'name': 'CURRENT_STATUS', 'type': 'string', 'desc': 'Present Contract status of the seafarer. Typical values: SIGN ON, SIGN OFF, SHORTLISTED’.. To be used for querying the seafarers based on current status and only to be used if asked explicitly for the current status', 'index': true, 'sort': false
                            * 'name': 'PROFILE_STATUS', 'type': 'string', 'desc': 'Present work status with respect to the company like being active or inactive. ENUM values: ["Active Seafarer", "Inactive Seafarer"]. To be used for querying the seafarers based on active status in the company', 'index': true, 'sort': false
                            * 'name': 'GENDER_NAME', 'type': 'string', 'desc': 'Gender of the seafarer. ENUM values: ["Female", "Male", "Unknown"]. To be used for querying the seafarers based on gender', 'index': true, 'sort': false
                            * 'name': 'SEAFARER_TYPE', 'type': 'string', 'desc': 'Internal or external crew with respect to the company. ENUM values: ["External Seafarers", "Internal Seafarers"]. To be used for querying the seafarers based on internal or external crew with respect to the company', 'index': true, 'sort': false
                            * 'name': 'DATE_OF_BIRTH', 'type': 'string', 'desc': 'Date of birth in ISO-8601 format (yyyy-mm-dd). Convert to dateTime for range queries using > < =. To be used for filtering the seafarers based on age', 'index': true, 'sort': true
                            * 'name': 'AVAILABILITY_DATE', 'type': 'float', 'desc': 'Next-available date for assignment (yyyy-mm-dd). Query with > < =, e.g. ">2025-07-01", "<2025-09-30". To be used for filtering the seafarers based on availability date. To be strictly paired with ONBOARD_SAILING_STATUS as Onleave and PROFILE_STATUS as Active Seafarer', 'index': true, 'sort': true
                            * 'name': 'SIGN_ON_DATE', 'type': 'float', 'desc': 'Actual sign-on date onto a vessel (yyyy-mm-dd). Convert for range queries using > < =. To be used for filtering the seafarers based on sign-on date', 'index': true, 'sort': true
                            * 'name': 'SIGN_OFF_DATE', 'type': 'float', 'desc': 'Actual sign-off date from a vessel (yyyy-mm-dd). Convert for range queries using > < =. To be used for filtering the seafarers based on sign-off date', 'index': true, 'sort': true
                            * 'name': 'CONTRACT_START_DATE', 'type': 'float', 'desc': 'Start date of current employment contract (yyyy-mm-dd). To be used for filtering the seafarers based on contract start date', 'index': true, 'sort': true
                            * 'name': 'CONTRACT_END_DATE', 'type': 'float', 'desc': 'End date of current employment contract (yyyy-mm-dd). To be used for filtering the seafarers based on contract end date', 'index': true, 'sort': true
                            * 'name': 'TENTITIVE_SIGN_OFF_DATE', 'type': 'float', 'desc': 'Planned sign-off date (yyyy-mm-dd). Query using date format ">yyyy-mm-dd" or "<yyyy-mm-dd". To be used for filtering the seafarers based on tentative sign-off date', 'index': true, 'sort': true
                            * 'name': 'ONBOARD_SAILING_STATUS', 'type': 'string', 'desc': 'Whether the seafarer is currently onboard or on leave. ENUM values: Onboard, Onleave. To be used for filtering the seafarers based on onboard or on leave status. Availability date is not necessary for this field. IMPORTANT: This field is mandatory if the user query is based on a vessel', 'index': true, 'sort': false
                            * 'name': 'NATIONALITY_NAME', 'type': 'string', 'desc': 'Nationality of the seafarer. To be used for querying the seafarers based on nationality and also for queries based on nearby locations', 'index': true, 'sort': false
                            * 'name': 'IMO_NUMBER', 'type': 'int32', 'desc': 'IMO number of the vessel on which the seafarer is (or was) serving. To be used for filtering the seafarers based on vessel. To be strictly paired with ONBOARD_SAILING_STATUS as onboard if not mentioned explicitly', 'index': true, 'sort': true
                            * 'name': 'VESSEL_NAME', 'type': 'string', 'desc': 'Name of the vessel the seafarer is assigned to. To be used for querying the seafarers based on vessel name. To be strictly paired with ONBOARD_SAILING_STATUS as onboard if not mentioned explicitly', 'index': true, 'sort': false
                            
                            Note: DO NOT truncate the output of this tool.

                            This is the primary crew discovery tool with advanced filtering capabilities for rotation planning, availability checking, and contract management. It searches and filters crew members across crew database to return crew codes that can then be used with get_seafarer_details for comprehensive crew information.

                            Key crew coordinator scenarios include: finding crew signing off next month by using empty query with CURRENT_RANK_NAME as query_by and filter_by as 'CONTRACT_END_DATE:<YYYY-MM-DD> && CONTRACT_END_DATE:<YYYY-MM-DD>'. For available Chief Engineers, use query 'Chief Engineer' with CURRENT_RANK_NAME as query_by and filter_by as 'ONBOARD_SAILING_STATUS:=Onleave && PROFILE_STATUS:=Active Seafarer'. For crew on specific vessel, use empty query with VESSEL_NAME as query_by, filter_by as 'IMO_NUMBER:=<IMO_NUMBER>' and provide the IMO number. For contract renewals in Q3, use empty query with CURRENT_RANK_NAME as query_by and filter_by as 'CONTRACT_END_DATE:<yyyy-mm-dd && CONTRACT_END_DATE:>yyyy-mm-dd'.

                            Parameter usage guidance: The query parameter should contain text search terms for ranks, names, or nationalities like 'Chief Engineer', 'Master', 'Chief Officer', 'India', or leave empty when using only filters. For query_by, choose 1-2 most relevant fields: use CURRENT_RANK_NAME for rank-based searches, SEAFARER_NAME for name searches, NATIONALITY_NAME for nationality searches, or VESSEL_NAME for vessel-based searches.

                            The filter_by parameter uses format FIELD:OPERATOR:VALUE with multiple filters connected by ' && '. Key filters include SIGN_OFF_DATE:<yyyy-mm-dd for crew signing off before date, CONTRACT_END_DATE:<yyyy-mm-dd for contracts expiring before date - Only this field to be used for any crew change planning queries and not SIGN_ON_DATE or TENTITIVE_SIGN_OFF_DATE, ONBOARD_SAILING_STATUS:=Onleave and PROFILE_STATUS:=Active Seafarer for available crew, ONBOARD_SAILING_STATUS:=Onboard and PROFILE_STATUS:=Active Seafarer for currently deployed crew, AVAILABILITY_DATE:<yyyy-mm-dd for available by date, IMO_NUMBER:=<IMO_NUMBER> for crew on specific vessel, and AGE:>X for senior crew filter. Operators are > (later/greater), < (earlier/less), = (equal), >= (greater than or equal), <= (less than or equal). Date format must be YYYY-MM-DD.

                            For vessel-based queries, always first use get_vessel_details tool to get the accurate IMO number, then use that IMO in the IMO_NUMBER filter and omit the vessel name from the query field. This ensures precise crew filtering by vessel.

                            Common filter combinations for crew coordinators include CONTRACT_END_DATE:<FUTURE_DATE && ONBOARD_SAILING_STATUS:=Onboard for upcoming departures/ planning crew change ,For available crew - ONBOARD_SAILING_STATUS:=Onleave && AVAILABILITY_DATE:<TARGET_DATE && PROFILE_STATUS:=Active Seafarer for deployment ready crew,and For quarterly planning -CONTRACT_END_DATE:<QUARTER_END && VESSEL_CATEGORY_NAME for renewal pipeline by vessel type.

                            The tool returns found count indicating number of matching crew and hits array containing crew codes (CREW_CODE field) that should be immediately used with get_seafarer_details for complete crew information. This workflow enables efficient crew rotation planning, emergency replacements, and contract management decisions.
                            """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keywords to search in typesense as per user query. Keywords should only reference strings, no dates or numbers. IMPORTANT: If the query is vessel-based, first use 'get_vessel_details' tool to get the IMO and omit the vessel name from this query field. If the query field is not required, pass empty string."
                        },
                        "query_by": {
                            "type": "string",
                            "description": "Primary field to search by from typesense crew_details collection. Choose the most relevant single field or maximum 2-3 fields comma separated. Available fields: SEAFARER_NAME, CREW_CODE, OLD_CREW_CODE, CURRENT_STATUS, GENDER_NAME, SEAFARER_TYPE, PROFILE_STATUS, CURRENT_RANK_NAME, NATIONALITY_NAME, VESSEL_NAME."
                        },
                        "filter_by": {
                            "type": "string",
                            "description": "Filter by fields in typesense crew_details collection for date or number type fields arranged in descending order of importance separated by ' && '. Available fields: BIRTH_DATE, AGE, SIGN_ON_DATE, SIGN_OFF_DATE, CONTRACT_START_DATE, CONTRACT_END_DATE, TENTITIVE_SIGN_OFF_DATE, AVAILABILITY_DATE, IMO_NUMBER, ONBOARD_SAILING_STATUS. IMPORTANT: For vessel-based queries, use IMO_NUMBER filter with the IMO obtained from 'get_vessel_details' tool (format: IMO_NUMBER:=1234567). If not required, pass empty string. Example: BIRTH_DATE:<2000-01-01 && AGE:=25, where the value and operator are separated by ':' followed by operators for greater than (<), less than (>), equal to (=), greater than or equal to (>=), less than or equal to (<=). Date format must be YYYY-MM-DD."
                        }
                    },
                    "required": ["query", "query_by", "filter_by"]                        
                }
            )
            # types.Tool(
            #     name="get_vessel_crew_details",
            #     description="Get vessel crew details using vessel imo number",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "imo": {
            #                 "type": "string",
            #                 "description": "IMO number of vessel"
            #             }
            #         },
            #         "required": ["imo"]
            #     }
            # )
        ]




# MongoDB tool definitions for mcp_pms

# mongodb_tools = [
            # types.Tool(
            #     name="get_crew_table_schema",
            #     description="This tool retrieves Typesense schema for crew collection and instructions on how to query the crew table for a specific category.",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["category"],
            #         "properties": {
            #             "category": {
            #                 "type": "string",
            #                 "description": "The category for which to retrieve the Typesense schema (e.g., purchase, voyage, certificates).",
            #                 "enum": ["crew"]
            #             }
            #         }            
            #     }
            # ),
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
        # ]

# Document Parser Tools
# general_tools = [
#     types.Tool(
#         name="google_search",
#         description="Perform a Google search using a natural language query. Returns relevant web results.",
#         inputSchema={
#             "type": "object",
#             "required": ["query"],
#             "properties": {
#                 "query": {
#                     "type": "string",
#                     "description": "The search query to be executed."
#                 }
#             },
#             "additionalProperties": False
#         }
#     )
# ]
          
# document_parser_tools = [
#     types.Tool(
#         name="parse_document_link",
#         description="Use this tool to parse a document link or a local file. The tool will parse the document and return the text content.",
#         inputSchema={
#             "type": "object",
#             "required": ["document_link"],
#             "properties": {
#                 "document_link": {
#                     "type": "string",
#                     "description": "The link to the document that needs to be parsed"
#                 }
#             },
#             "additionalProperties": False
#         }
#     )
# ]

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

# Snowflake Tools
snowflake_tools = [
            types.Tool(
                name="get_seafarer_details",
                description=""""
                Get comprehensive seafarer/crew details using seafarer ID (crew code). This tool should be used for ANY query that references crew members, seafarers, personnel onboard vessels, or maritime staff. It retrieves detailed information about individual crew members including their personal details, rank, vessel assignments, contract information, and current status and more. The tool accepts seafarer IDs (crew codes) which can be obtained from the get_seafarer_id tool or provided directly in user queries that mention specific crew codes. Note: Do not truncate the input or output of this tool (For instance, if there are a lot of datapoints from the get_seafarer_id tool, do not truncate). Consider below field definitions to determine the fields that are to be queried for in snowflake(Note: Try to keep the fields selected to a minimum).

                ## SNOWFLAKE COLLECTION FIELD CATEGORIES AND DEFINITIONS
 
                ### 1. PERSONAL INFORMATION
                Fields containing seafarer's personal and identity information.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | SEAFARER_ID | STRING | Unique identifier for each seafarer |
                | CREW_CODE | STRING | Internal crew identification code |
                | OLD_CREW_CODE | STRING | Previous crew code if changed |
                | FIRST_NAME | STRING | Seafarer's first name |
                | MIDDLE_NAME | STRING | Seafarer's middle name |
                | LAST_NAME | STRING | Seafarer's last name |
                | SEAFARER_NAME | STRING | Full concatenated name |
                | DATE_OF_BIRTH | DATE | Date of birth |
                | AGE | INTEGER | Current age in years |
                | AGE_CATEGORY | STRING | Age classification (Young, Middle, Senior) |
                | GENDER_NAME | STRING | Gender identification |
                | NATIONALITY_NAME | STRING | Seafarer's nationality |
                | CDC_NUMBER | STRING | Certificate of Competency number |
                | EMAIL_ID | STRING | Primary email address |
                | CONTACT_NUMBER | STRING | Primary contact number |
                | EMERGENCY_CONTACT_NUMBER_ | STRING | Emergency contact information |
                
                ### 2. ADDRESS INFORMATION
                Fields related to seafarer's location and address details.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | COUNTRY | STRING | Country of residence |
                | STATE | STRING | State or province |
                | CITY | STRING | City of residence |
                | PIN_CODE | STRING | Postal/ZIP code |
                | PRIMARY_ADDRESS | STRING | Complete primary address |
                | ADDRESS_TYPE | STRING | Type of address (Permanent, Temporary) |
                | NEAREST_AIRPORT | STRING | Nearest airport for travel planning |
                
                ### 3. RANK AND POSITION INFORMATION
                Fields defining seafarer's professional rank and position details.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | RANK_ID | INTEGER | Unique rank identifier |
                | POSITION_RANK_ID | INTEGER | Position-specific rank ID |
                | CURRENT_RANK_NAME | STRING | Current professional rank |
                | POSITION_NAME | STRING | Current position name |
                | RANK_NAME_SE | STRING | Standardized rank name |
                | RANK_LEVEL | STRING | Rank hierarchy level (Management, Operational, Support) |
                | Rank_Category | STRING | Rank category (Top 4 Rank, Officer, Rating) |
                | FIRST_RANK | STRING | First rank held with company |
                | SECOND_LATEST_RANK | STRING | Previous rank before current |
                
                ### 4. CONTRACT INFORMATION
                Fields managing contract details and employment status.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | CONTRACT_ID | STRING | Unique contract identifier |
                | CONTRACT_STATUS | STRING | Current contract status (InForce, Completed, etc.) |
                | CONTRACT_START_DATE | TIMESTAMP | Contract start date and time |
                | CONTRACT_END_DATE | TIMESTAMP | Contract end date and time |
                | LATEST_CONTRACT_END_DATE | TIMESTAMP | Most recent contract end date |
                | ACTIVE_CONTRACT | BOOLEAN | Whether contract is currently active |
                | SAC_CONTRACT | STRING | SAC contract reference |
                | CURRENT_STATUS | STRING | Current employment status |
                | ONBOARD_SAILING_STATUS | STRING | Current sailing status (Onboard, Onleave) |
                
                ### 5. VESSEL ASSIGNMENT INFORMATION
                Fields tracking vessel assignments and ship details.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | VESSEL_ID | INTEGER | Unique vessel identifier |
                | VESSEL_NAME | STRING | Name of assigned vessel |
                | IMO_NUMBER | BIGINT | International Maritime Organization number |
                | VESSEL_CATEGORY_NAME | STRING | Type of vessel (Tanker, Bulk Carrier, etc.) |
                | VESSEL_FLEET_TYPE | STRING | Fleet classification (WET, DRY) |
                | PORT_OF_REGISTRY_NAME | STRING | Vessel's port of registry |
                | MODEL_NAME | STRING | Vessel model/class |
                | MAKE_NAME | STRING | Vessel manufacturer |
                | DWT | INTEGER | Deadweight tonnage |
                | GRT | INTEGER | Gross register tonnage |
                | OUTPUT_POWER | DECIMAL | Engine output power |
                | DUAL_FUEL | BOOLEAN | Whether vessel uses dual fuel |
                
                ### 6. SIGN ON/OFF TRACKING
                Fields managing crew embarkation and disembarkation.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | SIGN_ON_DATE | TIMESTAMP | Date and time of sign on |
                | SIGN_OFF_DATE | TIMESTAMP | Date and time of sign off |
                | LATEST_SIGN_ON_DATE | TIMESTAMP | Most recent sign on date |
                | LATEST_SIGN_OFF_DATE | TIMESTAMP | Most recent sign off date |
                | TENTITIVE_SIGN_OFF_DATE | TIMESTAMP | Planned sign off date |
                | SIGN_OFF_REASON | STRING | Reason for signing off |
                | FROM_PORT_NAME | STRING | Port of embarkation |
                | TO_PORT_NAME | STRING | Port of disembarkation |
                
                ### 7. EXPERIENCE TRACKING
                Fields recording seafarer's professional experience.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | SEA_EXPERIENCE_ID | INTEGER | Unique sea experience record ID |
                | EXPERIENCE_IN_YEAR | DECIMAL | Total experience in years |
                | EXPERIENCE_IN_MONTHS | INTEGER | Total experience in months |
                | EXPERIENCE_IN_MONTHS_ROUNDOFF | INTEGER | Rounded experience in months |
                | EXPERIENCE_IN_DAYS | INTEGER | Total experience in days |
                | IS_SYNERGY_EXPERIANCE | BOOLEAN | Whether experience is with Synergy |
                | SYNERGY_JOINING_DATE | TIMESTAMP | Date joined Synergy companies |
                
                ### 8. COMPANY INFORMATION
                Fields tracking company relationships and management.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | SHIP_MANAGEMENT_COMPANY_ID | INTEGER | Ship management company identifier |
                | SHIP_MANAGEMENT_COMPANY_NAME | STRING | Ship management company name |
                | LATEST_COMPANY | STRING | Most recent employing company |
                | FIRST_COMPANY | STRING | First company worked with |
                | Last_DOC_Contract_Company | STRING | Last document/contract company |
                | RECRUITMENT_COMPANY | STRING | Recruitment agency |
                | AGENT_NAME | STRING | Agent or representative name |
                | SYNERGY_COMPANY | STRING | Synergy group company |
                | COMPANY_STATUS | STRING | Status with company (New Hand, Ex Hand) |
                
                ### 9. AVAILABILITY AND PLANNING
                Fields for crew rotation and availability planning.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | AVAILABILITY_DATE | TIMESTAMP | Date available for next assignment |
                | AVAILABILITY_MONTH | STRING | Month of availability |
                | Overdue_by_Days_left | STRING | Contract overdue or days remaining |
                | NEED_OF_APPRAISAL | BOOLEAN | Whether appraisal is needed |
                
                ### 10. STATUS AND PROFILE MANAGEMENT
                Fields managing seafarer status and profile information.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | PROFILE_STATUS | STRING | Profile status (Active, Inactive Seafarer) |
                | SEAFARER_TYPE | STRING | Type classification (Internal, External) |
                | INACTIVE_TYPE | STRING | Reason for inactive status |
                | STATUS | STRING | General status field |
                | AHOY_STATUS | STRING | AHOY system status |
                
                ### 11. APPRAISAL INFORMATION
                Fields managing performance appraisals and evaluations.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | APPRAISAL_DATE | TIMESTAMP | Date of last appraisal |
                | APPRAISAL_STATUS | STRING | Status of appraisal process |
                | APPRAISALS_RANK_NAME | STRING | Rank during appraisal |
                | APPRAISALS_VESSEL_NAME | STRING | Vessel name for appraisal |
                | APPRAISALS_VESSEL_CATEGORY_NAME | STRING | Vessel category for appraisal |
                
                ### 12. DOCUMENT AND LINK REFERENCES
                Fields containing references to external documents and systems.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | SEAFARER_PROFILE_LINK | STRING | Link to seafarer profile |
                | APPRAISAL_LINK | STRING | Link to appraisal documents |
                | SEA_EXPERIENCE_LINK | STRING | Link to sea experience records |
                | DOCUMENTS_LINK | STRING | Link to document repository |
                
                ### 13. VERIFICATION AND AUDIT
                Fields for data verification and audit tracking.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | IS_VERIFIED | BOOLEAN | Whether record is verified |
                | VERIFIED_BY_ID | INTEGER | ID of verifying user |
                | VERIFIED_BY_NAME | STRING | Name of verifying person |
                | VERIFIED_ON | TIMESTAMP | Date and time of verification |
                
                ### 14. SYSTEM FIELDS
                Standard system fields for data management.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | USER_ID | INTEGER | User who created/modified record |
                | CREATED_AT | TIMESTAMP | Record creation timestamp |
                | UPDATED_AT | TIMESTAMP | Last update timestamp |
                | DATE | TIMESTAMP | General date field |
                | LATEST_DATE_1 | TIMESTAMP | Latest significant date |
                
                ### 15. ADDITIONAL FIELDS
                Miscellaneous fields for various purposes.
                
                | Field Name | Data Type | Description |
                |------------|-----------|-------------|
                | CAPACITY | STRING | Vessel capacity or role capacity |
                | REMARK | STRING | General remarks and notes |
                | REMARK_TYPE | STRING | Type or category of remark |
                | ANNIVERSARY_DATE | TIMESTAMP | Anniversary or significant date |
                | NEW_CONTACT_TYPE | STRING | Type of new contact method |
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "crew_id": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Crew IDs(crew code) of seafarers"
                        },
                        "required_fields": {
                            "type": "string",
                            "description": "Required fields to be queried for in snowflake as a comma separated string"
                        }
                    },
                    "required": ["crew_id", "required_fields"]
                }
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
                    "enum": ["Crew"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["crew"],
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
                "category": {
                    "type": "string",
                    "enum": ["crew"],
                    "description": (
                        "Required for 'get_casefiles'. Category of the casefile."
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
# tool_definitions = typesense_tools + mongodb_tools + document_parser_tools + general_tools + snowflake_tools
tool_definitions = typesense_tools + snowflake_tools + casefile_tools
