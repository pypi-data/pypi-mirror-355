import mcp.types as types
from mcp_survey import mcp, logger

prompt_list = [
    types.Prompt(
        name="survey_server_operating_instructions",
        description="general instructions for the user to work with the Survey system",
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
            if name == "survey_server_operating_instructions":
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
                    text=f"""# Maritime Survey & Certification MCP Server

                            This MCP server is connected to the Shippalm (ERP) data, certiifcate table in typesense, mongodb database and external classification societies website data.
                            Shippalm (ERP) data is one of the sources for the vessel's survey and certification data.
                            Typesense is also used to search the certificate table and retrieve the certificate link or data like validity ,expiry date , window period start date, window period end date, etc for survey, certificates, COC (Condiiton of Class), IHM(Inventory of Hazardous Materials), etc.
                            MongoDB is used to store the vessel survey and certification data , also summaries and formatted data for the vessel survey and certification data.
                            External classification societies website data is used to get the certificate details using playwright browser automation tools.

                            ## Core Capabilities
                            - Retrieve vessel survey and certification data from Shippalm (ERP) data, certiifcate table in typesense, mongodb database and external classification societies website data.
                            - Check certificate expiry dates and validity periods  
                            - Access certificate documentation and links
                            - Playwright browser automation to access Shippalm (ERP) system and external classification societies website data.

                            ## Tool Operation
                            -The server operates through function-based tool calls where agents specify search parameters, vessel identifiers (IMO numbers), and desired data scope.
                            -Tools can be combined to build comprehensive vessel compliance pictures, from high-level overviews to detailed certificate-by-certificate analysis.
                            

                            ## Operating Guidelines
                            - Call get_vessel_details only if the imo number, class, or shippalmDoc parameters which are needed to answer the query, is missing.
                            - Always provide a brief overview - short answer first. Detailed answer or information to be given only if requested
                            - Use available tools to fetch real-time data from survey systems
                            - Focus on accuracy of expirty dates, window start and end dates, and compliance status
                            - Any links or data should always be provided in the response.
                            - Clarify vessel identification (IMO/name) when ambiguous queries are received
                            - For more complex queries,when other specialised tools don't return sufficient information, use smart_certificate_search tool to get more information from the certificate table in typesense. 
                            - Always get schema first using get_certificate_table_schema before using smart_certificate_search tool.

                            ## Available Tools
                            Your tools provide access to:
                            - Certificate expiry tracki
                            - Survey due date monitoring  
                            - Certificate document retrieval
                            - Shippalm (ERP) system access through playwright browser automation tools
                            - Vessel/Fleet details

                            You have direct access to live survey databases and should leverage your tools to provide current, accurate information for maritime compliance management.
                            """
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
