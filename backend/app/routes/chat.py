"""Chat endpoint for conversational AI interaction"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.middleware.auth import get_current_user_id, check_rate_limit
from app.agent.orchestrator import get_orchestrator
from app.agent.conversation_manager import get_conversation_manager
from app.mcp.server import get_available_tools
from app.mcp.tools.add_task import add_task_handler
from app.mcp.tools.list_tasks import list_tasks_handler
from app.mcp.tools.complete_task import complete_task_handler
from app.mcp.tools.delete_task import delete_task_handler
from app.mcp.tools.update_task import update_task_handler
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[int] = Field(None, description="Conversation ID (creates new if not provided)")


class ChatResponse(BaseModel):
    """Chat message response"""
    conversation_id: int
    response: str
    tool_calls: Optional[list] = None
    created_at: str


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    user_id: str,
    request: ChatRequest,
    current_user_id: str = Depends(check_rate_limit),
    session: Session = Depends(get_session)
):
    """
    Process a chat message with the AI assistant

    This endpoint:
    1. Validates user authentication and isolation
    2. Checks rate limits (100 requests/hour, 20/minute)
    3. Creates or retrieves conversation
    4. Retrieves conversation history for context
    5. Processes message with OpenAI agent
    6. Executes MCP tool calls if needed
    7. Stores user message and assistant response
    8. Returns response to user

    Args:
        user_id: User ID from path
        request: Chat request with message and optional conversation_id
        current_user_id: Authenticated user ID from JWT (with rate limit check)
        session: Database session

    Returns:
        ChatResponse with conversation_id, response, tool_calls, created_at

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If conversation_id doesn't exist
        HTTPException 400: If message validation fails
        HTTPException 429: If rate limit exceeded (100/hour or 20/minute)
        HTTPException 500: If processing fails
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Additional message validation (Pydantic already validates, but adding explicit check)
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )

    if len(request.message) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must be 10,000 characters or less"
        )

    conversation_manager = get_conversation_manager()
    orchestrator = get_orchestrator()

    # Step 1: Get or create conversation
    if request.conversation_id:
        try:
            conversation = conversation_manager.get_conversation(
                conversation_id=request.conversation_id,
                user_id=user_id,
                session=session
            )
            conversation_id = conversation.id
            logger.info(f"Using existing conversation {conversation_id}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
    else:
        conversation = conversation_manager.create_conversation(
            user_id=user_id,
            session=session
        )
        conversation_id = conversation.id
        logger.info(f"Created new conversation {conversation_id}")

    # Step 2: Retrieve conversation history
    try:
        history = conversation_manager.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            session=session
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    # Step 3: Get available tools
    tools = get_available_tools()

    # Step 4: Process message with agent
    try:
        agent_result = await orchestrator.process_message(
            user_id=user_id,
            message=request.message,
            conversation_history=history,
            tools=tools
        )
    except Exception as e:
        logger.error(f"Agent processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

    # Step 5: Execute tool calls if any
    tool_results = []
    if agent_result.get("tool_calls"):
        for tool_call in agent_result["tool_calls"]:
            try:
                # Parse arguments
                arguments = json.loads(tool_call["arguments"])

                # Add user_id to arguments
                arguments["user_id"] = user_id

                # Execute tool
                if tool_call["name"] == "add_task":
                    result = await add_task_handler(**arguments)
                    tool_results.append({
                        "tool": "add_task",
                        "result": result
                    })
                elif tool_call["name"] == "list_tasks":
                    result = await list_tasks_handler(**arguments)
                    tool_results.append({
                        "tool": "list_tasks",
                        "result": result
                    })
                elif tool_call["name"] == "complete_task":
                    result = await complete_task_handler(**arguments)
                    tool_results.append({
                        "tool": "complete_task",
                        "result": result
                    })
                elif tool_call["name"] == "delete_task":
                    result = await delete_task_handler(**arguments)
                    tool_results.append({
                        "tool": "delete_task",
                        "result": result
                    })
                elif tool_call["name"] == "update_task":
                    result = await update_task_handler(**arguments)
                    tool_results.append({
                        "tool": "update_task",
                        "result": result
                    })
                else:
                    logger.warning(f"Unknown tool: {tool_call['name']}")

            except Exception as e:
                logger.error(f"Tool execution failed: {str(e)}")
                tool_results.append({
                    "tool": tool_call["name"],
                    "error": str(e)
                })

    # Step 6: Get final response (call agent again with tool results if needed)
    final_response = agent_result.get("response", "")

    # If tools were called but no response, generate response with tool results
    if tool_results and not final_response:
        # Format tool results for agent
        tool_messages = history + [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": "", "tool_calls": agent_result.get("tool_calls", [])},
            {"role": "tool", "content": json.dumps(tool_results)}
        ]

        # Get final response from agent
        try:
            final_result = await orchestrator.process_message(
                user_id=user_id,
                message="",  # Empty message, agent uses tool results
                conversation_history=tool_messages,
                tools=None  # No more tool calls needed
            )
            final_response = final_result.get("response", "I've processed your request.")
        except Exception as e:
            logger.error(f"Failed to generate final response: {str(e)}")
            final_response = "I've completed the task."

    # Step 7: Store messages
    try:
        # Store user message
        conversation_manager.store_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=request.message,
            session=session
        )

        # Store assistant response
        conversation_manager.store_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=final_response,
            session=session
        )
    except Exception as e:
        logger.error(f"Failed to store messages: {str(e)}")
        # Don't fail the request if storage fails, but log it

    # Step 8: Return response
    return ChatResponse(
        conversation_id=conversation_id,
        response=final_response,
        tool_calls=tool_results if tool_results else None,
        created_at=datetime.utcnow().isoformat()
    )


__all__ = ["router"]
