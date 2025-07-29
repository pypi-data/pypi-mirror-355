"""
MCP PMS package initialization
"""

from mcp.server import Server
import logging
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .constants import (
    TYPESENSE_HOST,
    TYPESENSE_PORT,
    TYPESENSE_PROTOCOL,
    TYPESENSE_API_KEY,
    MONGODB_URI,
    MONGODB_DB_NAME,
)

# Initialize MCP Server instance
mcp = Server("mcp_pms")

# Define server configuration
def get_server_config():
    return InitializationOptions(
        server_name="mcp-pms",
        server_version="1.0.0",
        capabilities=mcp.get_capabilities(
            notification_options=NotificationOptions(resources_changed=True),
            experimental_capabilities={},
        ),
    )

__all__ = [
    'mcp',  # Export the MCP instance
    'get_server_config',  # Export the server configuration
    'TYPESENSE_HOST',
    'TYPESENSE_PORT',
    'TYPESENSE_PROTOCOL',
    'TYPESENSE_API_KEY',
    'MONGODB_URI',
    'MONGODB_DB_NAME',
    'logger'
] 