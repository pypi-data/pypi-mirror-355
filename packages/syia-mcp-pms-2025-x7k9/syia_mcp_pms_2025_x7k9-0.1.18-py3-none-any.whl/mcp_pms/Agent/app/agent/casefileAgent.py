from typing import Dict, List, Optional, Any
from pydantic import Field


from ...app.agent.toolcall import ToolCallAgent
from ...app.tool import Terminate, ToolCollection
from ...app.tool.mcp_tool import Server
from ...app.schema import ToolChoice, Message
from ...app.logger import logger
from datetime import datetime
from ...markdown_logger import MarkdownLogger

SYSTEM_PROMPT = """
You are a helpful assistant. Use the available tools to help answer user questions.
"""
NEXT_STEP_PROMPT = """
What should you do next to answer the user's question?
"""

RESPONSE_SUMMARY_PROMPT = """
## Your Task
Create a comprehensive response that:
1. Directly addresses the user's query.
2. Synthesizes all relevant information fromm what you have gathered so far
3. Presents findings in a clear, conversational manner
4. Highlights the most important details
5. Organizes information logically if there are multiple findings
6. Uses a professional but accessible tone

Respond directly to the user without mentioning the tools you used to gather this information.
Focus on providing the most useful and relevant answer based on the information you have gathered so far.
"""

class MainAgent(ToolCallAgent):
    """Agent for managing and tracking budget-related tasks.

    This agent specializes in handling budget management tasks, including creating budgets,
    tracking expenses, setting financial goals, generating spending reports, and providing
    financial insights. It helps users manage their financial resources effectively,
    monitor spending patterns, and make informed financial decisions.
    """
    name: str = "main_agent"
    description: str = (
        "An agent that helps users create and manage budgets, track expenses, "
        "set financial goals, generate spending reports, and provide financial insights."
    )
    imo: Optional[str] = Field("", description="IMO number of the vessel")
    vessel_name: Optional[str] = Field("", description="Name of the vessel")
    markdown_logger: MarkdownLogger = Field(default_factory=MarkdownLogger)
    session_id: str = Field("", description="Session ID")
  

    max_observe: int = 10000
    max_steps: int = 20

    # Budget tracking information
    active_budget_id: Optional[str] = None
    current_step_index: Optional[int] = None
    past_step_indices: List[int] = Field(default_factory=list)
    collected_urls: List[str] = Field(default_factory=list)

    # Track the current thought index for linking actions to thoughts
    current_thought_index: Optional[int] = None

    # Add basic tools to the tool collection - will be enhanced later with budget tools
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Terminate()
        )
    )

    # Use Auto for tool choice to allow both tool usage and free-form responses
    tool_choices: ToolChoice = ToolChoice.AUTO
    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    # Track which MCP servers this agent is connected to
    connected_servers: dict[str, Server] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        

    async def process(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Process a prompt using the budget agent with context.

        Args:
            prompt: The user prompt to process
            context: Additional context like userId, category, and request_id

        Returns:
            The result of processing the prompt
        """
        if context is None:
            context = {}

        # Extract context information
        user_id = context.get("userId")
        category = context.get("category")
        request_id = context.get("request_id")

      
        if user_id or category:
            context_info = "\n\nContext information:\n"
            if user_id:
                context_info += f"- User ID: {user_id}\n"
            if category:
                context_info += f"- Category: {category}\n"

            context_info += "\nUse this context information when processing requests."
            enhanced_prompt = context_info + "\n\nUser query: " + prompt
            enhanced_prompt = enhanced_prompt
        # Process with the enhanced prompt
        result = await super().run(request=enhanced_prompt)
        return result

    def add_tool(self, tool):
        """Add a tool to the agent's available tools"""
        self.available_tools.add_tool(tool)
        logger.info(f"Added tool: {tool.name} to agent")

    def remove_tool(self, tool):
        """Remove a tool from the agent's available tools"""
        self.available_tools.remove_tool(tool)
        logger.info(f"Removed tool: {tool.name} from Budget agent")
    
    async def summarize_results(self, raw_result: str, original_query: str) -> str:
        """
        Summarize the step-by-step results into a coherent, user-friendly response.

        Args:
            raw_result: The raw step-by-step results from the agent's execution
            original_query: The original user query

        Returns:
            A summarized response that directly addresses the user's query
        """
        

        response_format = f"""## Original User Query
        {original_query}
        
        ## Stepwise Results
        {raw_result}"""

        # Prepare the prompt with the user query and raw results
        prompt = response_format +RESPONSE_SUMMARY_PROMPT.format(
            user_query=original_query,
            raw_results=raw_result
        )

        try:
            # Create messages for the LLM
            messages = [
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content=prompt)
            ]

            # Call the LLM to generate the summary
            summary = await self.llm.ask(messages=messages)

            return summary
        except Exception as e:
            logger.error(f"Error generating summarized response: {str(e)}")
            # If summarization fails, return the raw results with a note
            return f"Here are the details I found:\n\n{raw_result}"

    async def process_request(self, request: Optional[str] = None ) -> str:
        """Run the agent with cleanup when done"""
        try:
            # Add available tools to the request context
            if request:
                logger.warning(f"request: {request}")
            else:
                raise ValueError("Request is required")

    

            current_date = datetime.now().strftime("%Y-%m-%d")
            request += f"Current date: {current_date}"

            # Execute the agent to get raw step-by-step results
            raw_result = await super().run(request)
            self.markdown_logger.write("Raw Result", raw_result)
            return raw_result
        
        except Exception as e:
            logger.error(f"Error during agent run: {e}")
            return "Error during execution"
        finally:
            pass

    async def think(self) -> bool:
        """Override think to document agent thoughts"""
        # Get current message to use as thought content
        if self.messages and len(self.messages) > 0:
            last_message = self.messages[-1]

        logger.info(f"Agent think() called, current_step_index={self.current_step_index}, active_budget_id={self.active_budget_id}")

        # Call parent implementation
        result = await super().think()

        return result
