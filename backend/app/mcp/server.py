"""MCP Server initialization and tool registration"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from app.config import settings
from app.mcp.tools.add_task import add_task_handler, ADD_TASK_SCHEMA
from app.mcp.tools.list_tasks import list_tasks_handler, LIST_TASKS_SCHEMA
from app.mcp.tools.complete_task import complete_task_handler, COMPLETE_TASK_SCHEMA
from app.mcp.tools.delete_task import delete_task_handler, DELETE_TASK_SCHEMA
from app.mcp.tools.update_task import update_task_handler, UPDATE_TASK_SCHEMA
import logging

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp_server = Server(settings.MCP_SERVER_NAME)


def register_tools():
    """Register all MCP tools with the server"""

    # Register all tools
    @mcp_server.call_tool()
    async def handle_tools(name: str, arguments: dict):
        """Handle tool invocations"""
        if name == "add_task":
            logger.info(f"Executing add_task with arguments: {arguments}")
            result = await add_task_handler(**arguments)
            logger.info(f"add_task result: {result.get('success', False)}")
            return result
        elif name == "list_tasks":
            logger.info(f"Executing list_tasks with arguments: {arguments}")
            result = await list_tasks_handler(**arguments)
            logger.info(f"list_tasks result: {result.get('success', False)}")
            return result
        elif name == "complete_task":
            logger.info(f"Executing complete_task with arguments: {arguments}")
            result = await complete_task_handler(**arguments)
            logger.info(f"complete_task result: {result.get('success', False)}")
            return result
        elif name == "delete_task":
            logger.info(f"Executing delete_task with arguments: {arguments}")
            result = await delete_task_handler(**arguments)
            logger.info(f"delete_task result: {result.get('success', False)}")
            return result
        elif name == "update_task":
            logger.info(f"Executing update_task with arguments: {arguments}")
            result = await update_task_handler(**arguments)
            logger.info(f"update_task result: {result.get('success', False)}")
            return result

    logger.info("Registered MCP tools: add_task, list_tasks, complete_task, delete_task, update_task")


def get_mcp_server() -> Server:
    """
    Get the initialized MCP server instance

    Returns:
        Server: MCP server instance
    """
    return mcp_server


def get_available_tools():
    """
    Get list of available MCP tools for OpenAI agent

    Returns:
        List of tool schemas in OpenAI function format
    """
    return [
        {
            "type": "function",
            "function": {
                "name": ADD_TASK_SCHEMA["name"],
                "description": ADD_TASK_SCHEMA["description"],
                "parameters": ADD_TASK_SCHEMA["parameters"]
            }
        },
        {
            "type": "function",
            "function": {
                "name": LIST_TASKS_SCHEMA["name"],
                "description": LIST_TASKS_SCHEMA["description"],
                "parameters": LIST_TASKS_SCHEMA["parameters"]
            }
        },
        {
            "type": "function",
            "function": {
                "name": COMPLETE_TASK_SCHEMA["name"],
                "description": COMPLETE_TASK_SCHEMA["description"],
                "parameters": COMPLETE_TASK_SCHEMA["parameters"]
            }
        },
        {
            "type": "function",
            "function": {
                "name": DELETE_TASK_SCHEMA["name"],
                "description": DELETE_TASK_SCHEMA["description"],
                "parameters": DELETE_TASK_SCHEMA["parameters"]
            }
        },
        {
            "type": "function",
            "function": {
                "name": UPDATE_TASK_SCHEMA["name"],
                "description": UPDATE_TASK_SCHEMA["description"],
                "parameters": UPDATE_TASK_SCHEMA["parameters"]
            }
        }
    ]


async def start_mcp_server():
    """
    Start the MCP server with stdio transport

    This function initializes and runs the MCP server that provides
    task management tools to the OpenAI agent.
    """
    logger.info(f"Starting MCP server: {settings.MCP_SERVER_NAME} v{settings.MCP_SERVER_VERSION}")

    # Register tools before starting
    register_tools()

    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


# Register tools on import
register_tools()

# Export server instance for tool registration
__all__ = ["mcp_server", "get_mcp_server", "start_mcp_server", "get_available_tools"]
