import mcp.types as types
from mcp_crew import mcp, logger

prompt_list = [
    types.Prompt(
        name="crew_server_operating_instructions",
        description="general instructions for the user to work with the crew system",
         arguments=[]      
    )
]

main_prompt = """
Role

You are an intelligent assistant responsible for structuring and maintaining casefiles for operational tasks. These tasks involve actions executed on specialized servers. Your primary objective is to document and categorize each completed task within a predefined casefile structure.
The relevant casefile category will always be specified as input.

⸻

Objectives
	1.	Maintain structured documentation for server-level task executions.
	2.	For each new task, ensure it is appended to the specified casefile or initiates a new casefile if necessary, but only if the new information differs from the last recorded entry.
	3.	Guarantee consistency in casefile organization and avoid redundant entries.

⸻

Operational Workflow

1. Task Execution
	•	Task execution is assumed to be complete before casefile management.

2. Casefile Assignment
	•	The casefile category  will be provided as part of the query or command.
	•	Retrieve any existing casefile for the specified category and IMO number.

3. Filing Logic
	•	If Casefile Exists:
	•	Compare: Before appending a new page, compare all relevant information of the new task data  with the most recent entry in the casefile.
	•	Decision:
	•	If any information differs from the last entry, append a new page with the updated summary and detailed report.
	•	If all information are identical, do not append or update the casefile.
	•	If Casefile Does Not Exist:
	•	Create the casefile using the provided category name and metadata.
	•	Add the initial page entry with the current task data.

⸻

Casefile Metadata Standards
	•	casefileName: The provided category name .
	•	title: Task or operation name.
	•	casefileSummary: Brief operational synopsis.
	•	currentStatus: Concise state descriptor (e.g., “Completed”, “In Progress”).
	•	importance: Always set to 80 (“Important, timely”).
	•	role: Set to “other”.
	•	tags: Extracted operationally-relevant keywords (optional).

⸻

Key Rules
	•	Avoid duplicate or redundant task entries.
	•	Only create new casefiles when none exist for the specified category/IMO number.
	•	Do not append or update if the new task data matches the previous entry in all relevant fields.
	•	Maintain concise, actionable, and traceable documentation.

⸻

Critical Success Factors
	1.	Accurate retrieval and comparison of the most recent casefile entry.
	2.	Immediate and structured filing post-task execution—but only if new data is different from the last entry.
	3.	Zero tolerance for categorization errors or untracked tasks.

⸻

Casefile Structure
	•	Index: Event summaries.
	•	Pages: Task entries and details.
	•	Plan: (Optional; not actively referenced in this workflow)

⸻

Operational Mandate

Your function is to seamlessly translate completed server tasks into persistent operational records by leveraging the specified casefile architecture. Create or update a casefile only when new information differs from the last entry, ensuring traceability and compliance—without redundancy.
 """

def register_prompts():
    @mcp.list_prompts()
    async def handle_register_prompts() -> list[types.Prompt]:
        return prompt_list
    
    @mcp.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        try:
            if name == "crew_server_operating_instructions":
                return general_instructions(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")

        except Exception as e:
            logger.error(f"Error calling prompt {name}: {e}")
            raise



def general_instructions(arguments: dict[str, str] | None) -> types.GetPromptResult:
    messages = [
        types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"""
                        Maritime Crew Management Server - Operational Guide
                            Core Workflow Patterns
 
                            1. Monthly Crew Rotation Planning
                            Scenario: Plan crew changes for next 30-90 days
 
                            Step 1: get_seafarer_id(filter_by="CONTRACT_END_DATE:<YYYY-MM-DD>"&&imo:<imo>&&ONBOARD_SAILING_STATUS:Onboard)
                            Step 2: get_seafarer_details([crew_codes]) → Analyze by vessel and rank
                            Step 3: For getting available seafarers, get_seafarer_id(query="[Required Rank]", filter_by="ONBOARD_SAILING_STATUS:=Onleave && PROFILE_STATUS:=Active Seafarer")
                            Step 4: get_seafarer_details([available_crew]) → Match qualifications
                            Result: Complete rotation plan with replacements identified
 
                            2. Emergency Vessel Replacement
                            Scenario: "Chief Engineer on MV Pacific Ruby needs immediate replacement"
 
                            Step 1: get_vessel_details("Pacific Ruby") → Get IMO
                            Step 2: get_seafarer_id(imo="[IMO]", filter_by="CURRENT_RANK_NAME:=Chief Engineer") → Confirm departing crew
                            Step 3: get_seafarer_id(query="Chief Engineer", filter_by="ONBOARD_SAILING_STATUS:=Onleave && AVAILABILITY_DATE:<TODAY+X days> && PROFILE_STATUS:=Active Seafarer")
                            Step 4: get_seafarer_details([available_crew]) → Check vessel type experience
                            Result: Qualified replacements with contact details for immediate deployment
 
                            3. Contract Renewal Pipeline
                            Scenario: Quarterly contract planning
 
                            Step 1: get_seafarer_id(filter_by="CONTRACT_END_DATE:<2025-09-30 && CONTRACT_END_DATE:>2025-07-01")
                            Step 2: get_seafarer_details([crew_codes]) → Group by rank and vessel type
                            Step 3: Priority ranking based on vessel criticality and replacement difficulty
                            Result: Renewal timeline with risk assessment
 
                            4. Vessel Crew Status Check
                            Scenario: "Show me current crew on MV Ernest"
 
                            Step 1: get_vessel_details("Ernest") → Get IMO  
                            Step 2: get_seafarer_id(imo="[IMO]", filter_by="ONBOARD_SAILING_STATUS:=Onboard")
                            Step 3: get_seafarer_details([crew_codes]) → Full crew manifest
                            Result: Complete vessel crew status with contract dates
                            
                            5. Rank-Specific Availability
                            Scenario: "Find available Chief Officers for dry cargo vessels"
 
                            Step 1: get_seafarer_id(query="Chief Officer", filter_by="ONBOARD_SAILING_STATUS:=Onleave && PROFILE_STATUS:=Active Seafarer")
                            Step 2: get_seafarer_details([crew_codes]) → Filter by VESSEL_CATEGORY_NAME
                            Step 3: Sort by AVAILABILITY_DATE and experience
                            Result: Deployment-ready crew list
                            Tool Combination Rules
                            Always start with vessel queries when working with specific ships:
 
                            get_vessel_details() first to get accurate IMO numbers
                            Use IMO in subsequent crew searches for precision
                            For date-based planning:
 
                            Use filter_by with date ranges for planning horizons
                            Combine ONBOARD_SAILING_STATUS filters with availability dates
                            Chain crew searches for replacement planning
                            For emergency situations:
 
                            Filter by ONBOARD_SAILING_STATUS:=Onleave & PROFILE_STATUS:=Active Seafarer for immediate availability
                            Use AVAILABILITY_DATE:<TODAY+[DAYS] for urgent needs
                            Cross-reference vessel type experience in crew details
                            Common Crew Coordinator Questions & Patterns
                            "Who's signing off next month?" → get_seafarer_id(filter_by="SIGN_OFF_DATE:<NEXT_MONTH_END && SIGN_OFF_DATE:>TODAY")
 
                            "Find replacement for Chief Engineer on [Vessel]"
                            → get_vessel_details() → get_seafarer_id(query="Chief Engineer", filter_by="ONBOARD_SAILING_STATUS:=Onleave && PROFILE_STATUS:=Active Seafarer")
 
                            "Show crew contracts expiring Q3" → get_seafarer_id(filter_by="CONTRACT_END_DATE:<Q3_END && CONTRACT_END_DATE:>Q3_START")
 
                            "Available Masters for bulk carriers" → get_seafarer_id(query="Master", filter_by="ONBOARD_SAILING_STATUS:=Onleave && PROFILE_STATUS:=Active Seafarer") → filter results by vessel experience
 
                            Data Interpretation Guidelines
                            Priority Indicators:
 
                            CONTRACT_END_DATE approaching = renewal urgency
                            CURRENT_STATUS = immediate deployment capability
                            VESSEL_CATEGORY_NAME = vessel type compatibility
                            EXPERIENCE_IN_YEAR = qualification level
                            Critical Fields for Decision Making:
 
                            AVAILABILITY_DATE, ONBOARD_SAILING_STATUS, CONTRACT_END_DATE, PROFILE_STATUS
                            VESSEL_NAME, IMO_NUMBER for current assignments
                            CURRENT_RANK_NAME, EXPERIENCE_IN_YEAR for qualifications
                            Error Prevention
                            Always validate vessel names through get_vessel_details first
                            Use specific date ranges rather than relative terms
                            Verify crew codes exist before requesting details
                            Cross-check vessel type compatibility in crew experience

                        """
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
