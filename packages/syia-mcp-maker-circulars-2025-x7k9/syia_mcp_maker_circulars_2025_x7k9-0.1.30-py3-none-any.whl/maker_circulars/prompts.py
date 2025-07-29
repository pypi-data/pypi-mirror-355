import mcp.types as types
from maker_circulars import mcp, logger
import datetime

prompt_list = [
    types.Prompt(
        name="general_instructions",
        description="general instructions for the user to work with the Circular system",
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
            if name == "general_instructions":
                return general_instructions(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")

        except Exception as e:
            logger.error(f"Error calling prompt {name}: {e}")
            raise



def general_instructions(arguments: dict[str, str] | None) -> types.GetPromptResult:
    today = datetime.date.today().strftime('%Y-%m-%d')
    messages = [
        types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"You are a helpful assistant that can answer questions about the Circular. Today's date is {today}."
                ),
            ),
    ]
    return types.GetPromptResult(messages=messages)
