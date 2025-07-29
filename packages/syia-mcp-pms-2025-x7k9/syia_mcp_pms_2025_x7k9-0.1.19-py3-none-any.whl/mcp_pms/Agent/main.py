import asyncio
from .app.logger import logger, log_file_path
from .app.schema import Message

import asyncio
import os
import json
from contextlib import AsyncExitStack
import shutil
from pathlib import Path
from datetime import datetime, timezone
from .markdown_logger import MarkdownLogger
from .app.llm import LLM
from .app.toolHandler import ServerToolAdapter

import sys
from .app.agent.casefileAgent import MainAgent
from ..tool_schema import tool_definitions
from ..tools import handle_call_tool
from uuid import uuid4
import time
from pymongo import MongoClient
from ..Agent.markdown_logger import set_session_id, get_markdown_logger
from ..prompts import main_prompt


# Path to your config file (adjust as needed)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "mcp_servers_config.json")
def load_env_from_json(json_path):
    with open(json_path, 'r') as f:
        config = json.load(f)
    for key, value in config.items():
        os.environ[key] = str(value)
    return config

# Load environment variables from config
config = load_env_from_json(CONFIG_PATH)
 





def generate_session_id():
    timestamp = int(time.time())
    random_part = uuid4().hex[:8]
    return f"{timestamp}{random_part}"

async def main(payload):
    config = load_env_from_json(CONFIG_PATH)
    user_prompt = payload["query"]
    logger.info(f"User prompt: {user_prompt}")

    ## intialize the agent
    session_id = generate_session_id()
    set_session_id(session_id)
    markdown_logger = get_markdown_logger(session_id)
    casefile_agent = MainAgent(
        session_id=session_id,
        markdown_logger=markdown_logger,
        system_prompt= main_prompt
    )


    # Add all tools from tool_schema, wrapped in ServerToolAdapter
    for tool in tool_definitions:
        adapter = ServerToolAdapter(
            tool_name=tool.name,
            description=tool.description,
            input_schema=tool.inputSchema
        )
        casefile_agent.add_tool(adapter)

    response = await casefile_agent.run(user_prompt)
    logger.info(f"Final response received from agent")

    return response







