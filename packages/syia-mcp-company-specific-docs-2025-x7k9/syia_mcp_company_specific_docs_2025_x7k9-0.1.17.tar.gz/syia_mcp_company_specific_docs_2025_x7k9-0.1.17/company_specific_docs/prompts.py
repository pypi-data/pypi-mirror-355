import mcp.types as types
from company_specific_docs import mcp, logger

prompt_list = [
    types.Prompt(
        name="company_docs_instructions",
        description="Instructions for using the company docs tools should be always referred before using the tools available in company docs server.",
         arguments=[]      
    )
]

def register_prompts():
    """Register all prompts with the MCP server."""
    @mcp.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """List all available prompts."""
        logger.info("Listing available prompts")
        return prompt_list
    
    @mcp.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        """Get a specific prompt by name with the given arguments."""
        logger.info(f"Getting prompt: {name} with arguments: {arguments}")
        try:
            if name.strip().lower() == "company_docs_instructions".lower():
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
                    text=f"""Company Document Search Strategy
                            Iterative Search Approach - Never Stop at First Failure:

                            Start with vector search using fetch_company_documents_by_vector_search with user's query
                            If no results: Try smart_company_manual_search with rephrased queries (synonyms, related terms)
                            If still limited: Use list_company_manuals and get_by_company_document_name_or_num with partial names
                            Explore structure: Use get_company_manual_structure and get_company_manual_chapter_overview for promising documents
                            Read targeted sections: Use read_company_manual_section for identified relevant content
                            For forms/checklists: Try variations like "form", "checklist", "template" with document type filters
                            Cross-reference: Search across multiple document types and combine information from various sources
                            Final step: If information incomplete, explain what was searched and suggest alternatives
                            Always include sources: When providing answers, include relevant clickable links to the documents/sections from which the information was generated"""
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
