
import logging
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file if it exists
load_dotenv()

mcp = FastMCP()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when there's an error in the configuration."""
    pass

def get_required_env_var() -> str:
    """Get required environment variable or raise ConfigurationError if not found."""
    value = os.getenv('Token')
    if not value:
        raise ConfigurationError(f"Required environment variable Token is not set")
    return value


# Register the tool with MCP
@mcp.tool()
def query_demo_data(sql_query: str) -> Dict[str, Any]:
    """
    Query Demo data using BigQuery SQL syntax.

    Use this tool when you want to run SQL queries on demo data.
    The demo data is accessible via BigQuery, and the query must be written using BigQuery SQL dialect.
    Use this tool when:
    - You need to analyze data and extract high-level takeaways or trends
    - You want to generate natural language summaries, observations, or annotations
    - A user request or follow-up question depends on understanding the result of a SQL query

    Args:
        sql_query (str): A valid SQL query written in BigQuery dialect.

    """
    token = get_required_env_var()
    return "Hello World", token






# Run the MCP server locally

if __name__ == '__main__':
    # Run the async function
    # asyncio.run(query_connectors("vairb", "SELECT * FROM stripe.price LIMIT 100"))
    # asyncio.run(create_single_value_block("e20f4cce-23f0-414e-97b3-69a16ece9a47", "vairb", "Total Contacts", "SELECT COUNT(*) as total_contacts FROM hubspot.contacts"))

    mcp.run(transport="stdio")