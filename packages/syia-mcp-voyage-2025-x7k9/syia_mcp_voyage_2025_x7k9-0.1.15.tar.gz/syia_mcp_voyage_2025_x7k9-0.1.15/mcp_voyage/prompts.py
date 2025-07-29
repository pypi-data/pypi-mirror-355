import mcp.types as types
from . import mcp, logger

prompt_list = [
    types.Prompt(
        name="voyage_server_operating_instructions",
        description="general instructions for the user to work with the voyage related information",
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
            if name == "voyage_server_operating_instructions":
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
                    text=f"""# Maritime Voyage & Operations MCP Server

                    This MCP server is connected to the MongoDB database, Typesense voyage collection, real-time vessel tracking systems, and external weather APIs. It provides comprehensive voyage management, operational monitoring, and vessel performance data.

                    MongoDB is used to store pre-computed voyage summaries, fuel consumption data, cargo activity details, and operational reports.
                    Typesense voyage collection contains daily and historical voyage records with fuel consumption, ROB data, weather information, and operational details.
                    Real-time tracking systems provide live vessel positions, ETAs, and navigation data.
                    External weather APIs deliver current weather conditions at vessel locations.

                    ## Core Capabilities

                    - Real-time vessel position tracking and ETA monitoring
                    - Fuel consumption analysis and ROB (Remaining On Board) tracking
                    - Voyage planning and cargo activity monitoring  
                    - Weather data retrieval for vessel locations
                    - Charter party compliance assessment
                    - Fresh water production and consumption monitoring
                    - Lubricating oil consumption tracking (ME cylinder oil, MECC, AECC)
                    - Historical voyage data analysis and trend reporting

                    ## Tool Operation

                    The server operates through function-based tool calls where agents specify vessel identifiers (IMO numbers), time periods, and desired data scope.
                    Tools can be combined to build comprehensive operational pictures, from real-time status to historical performance analysis.
                    Many tools return pre-computed answers from MongoDB for immediate response.

                    ## Operating Guidelines

                    - Call get_vessel_details only if the IMO number is missing or vessel identification is unclear
                    - Use real-time tools (get_vessel_live_position_and_eta) before weather tools for current conditions
                    - For weather data, always call get_vessel_live_position_and_eta first to get coordinates and timestamp, then use get_live_weather_by_coordinates
                    - Leverage pre-computed MongoDB answers for quick responses on consumption, ROB, and voyage details
                    - Use Typesense voyage_table_search for complex historical analysis or trend identification
                    - Always get schema first using get_voyage_table_schema before using voyage_table_search
                    - Focus on operational efficiency and fuel management insights
                    - Provide actionable information for voyage optimization

                    ## Available Tools

                    Your tools provide access to:

                    - **Real-time Operations**: Live vessel positions, ETAs, cargo activity status
                    - **Fuel Management**: Consumption rates, ROB levels, bunker analysis across all fuel types
                    - **Lubricating Oils**: ME cylinder oil, MECC, AECC consumption and ROB tracking
                    - **Weather Services**: Current conditions at vessel locations using coordinates and timestamps
                    - **Voyage Planning**: Route details, port calls, charter party compliance
                    - **Performance Analytics**: Historical trends, efficiency metrics, operational patterns
                    - **Fresh Water Systems**: Production, consumption, and ROB monitoring
                    - **Cargo Operations**: Loading/discharging status, port activities

                    You have direct access to live operational databases and should leverage your tools to provide current, accurate information for maritime voyage management and operational decision-making.

                    """
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
