"""MCP Tool registration helpers and utilities"""
from typing import Callable, Any, Dict
from mcp.server import Server
from mcp.types import Tool
import logging

logger = logging.getLogger(__name__)


def register_tool(
    server: Server,
    name: str,
    description: str,
    parameters: Dict[str, Any],
    handler: Callable
) -> None:
    """
    Register an MCP tool with the server

    Args:
        server: MCP server instance
        name: Tool name (e.g., "add_task")
        description: Tool description for the AI agent
        parameters: JSON schema for tool parameters
        handler: Async function that handles tool invocation

    Example:
        register_tool(
            server=mcp_server,
            name="add_task",
            description="Create a new task for the user",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["user_id", "title"]
            },
            handler=add_task_handler
        )
    """
    tool = Tool(
        name=name,
        description=description,
        inputSchema=parameters
    )

    @server.call_tool()
    async def handle_tool_call(tool_name: str, arguments: Dict[str, Any]):
        if tool_name == name:
            logger.info(f"Executing tool: {name} with arguments: {arguments}")
            try:
                result = await handler(**arguments)
                logger.info(f"Tool {name} executed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {name} execution failed: {str(e)}")
                raise

    logger.info(f"Registered MCP tool: {name}")


def create_tool_schema(
    name: str,
    description: str,
    properties: Dict[str, Dict[str, Any]],
    required: list[str]
) -> Dict[str, Any]:
    """
    Create a JSON schema for an MCP tool

    Args:
        name: Tool name
        description: Tool description
        properties: Parameter properties (name -> schema)
        required: List of required parameter names

    Returns:
        Complete tool schema dictionary

    Example:
        schema = create_tool_schema(
            name="add_task",
            description="Create a new task",
            properties={
                "user_id": {"type": "string", "description": "User identifier"},
                "title": {"type": "string", "description": "Task title"}
            },
            required=["user_id", "title"]
        )
    """
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }


__all__ = ["register_tool", "create_tool_schema"]
