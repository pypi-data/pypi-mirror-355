import mcp.types as types
from . import mcp, logger

prompt_list = [
    types.Prompt(
        name="casefile_server_use_inspructions",
        description="use this instruction to use the casefile server tools, always use the get prompt tool to first get the casefile_server_use_inspructions promtp before using the tools in this server",
         arguments=[]      
    )
]



def register_prompts():
    @mcp.list_prompts()
    async def handle_register_prompts() -> list[types.Prompt]:
        return prompt_list
    
    @mcp.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        try:
            if name == "casefile_server_use_inspructions":
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
                    text=f"""The casefile system uses a two-tier architecture:

                        Typesense: For fast searching and discovery of casefiles
                        MongoDB: For storing detailed casefile content, pages, and plans

                        CRITICAL WORKFLOW - ALWAYS FOLLOW THIS ORDER:
                        Step 1: Search for Casefiles (Typesense)
                        ALWAYS start with smart_casefile_search to find relevant casefiles. This tool searches the Typesense database and returns:

                        _id: MongoDB ObjectId (REQUIRED for subsequent queries)
                        casefile: Title/name of the casefile
                        vesselName: Associated vessel
                        summary: Brief description
                        link: External reference link
                        Other metadata (dates, importance, category)

                        Important: The _id field from search results is the MongoDB ObjectId you MUST use for all subsequent MongoDB queries.
                        Step 2: Explore Casefile Details (MongoDB)
                        Once you have the _id from search results, use these tools to get detailed information:

                        get_casefile_index - Get the table of contents

                        Pass the _id as casefile_id
                        Returns list of pages with summaries
                        Use limit and next_iter for pagination
                        Each index entry shows: pagenum, summary, type, createdAt


                        get_casefile_pages - Get specific page content

                        Pass the _id as casefile_id
                        Pass array of page numbers (e.g., [0, 1, 2])
                        Returns full content for requested pages
                        Each page contains: content, flag, importance, links


                        get_latest_plan - Get the action plan

                        Pass the _id as casefile_id
                        Returns the most recent plan with: dateTime, flag, plan content



                        """
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
