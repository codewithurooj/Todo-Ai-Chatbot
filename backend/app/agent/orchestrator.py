"""OpenAI Agent Orchestrator for processing chat messages"""
from openai import OpenAI, OpenAIError, APIError, APIConnectionError, RateLimitError, AuthenticationError
from typing import List, Dict, Any, Optional
from app.config import settings
from app.agent.system_prompt import get_system_prompt
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class AgentOrchestrator:
    """
    Orchestrates AI agent processing for conversational task management

    Handles:
    - Message formatting for OpenAI API
    - Tool call processing
    - Response generation
    - Context management
    """

    def __init__(self, model: str = None, temperature: float = 0.7):
        """
        Initialize the agent orchestrator

        Args:
            model: OpenAI model to use (defaults to settings.OPENAI_MODEL)
            temperature: Sampling temperature (0.0-2.0, default 0.7)
        """
        self.model = model or settings.OPENAI_MODEL
        self.temperature = temperature
        self.client = client

    def format_messages(
        self,
        conversation_history: List[Dict[str, str]],
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        Format conversation history and current message for OpenAI API

        Args:
            conversation_history: List of previous messages
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            current_message: The new user message

        Returns:
            Formatted messages array including system prompt
        """
        messages = [{"role": "system", "content": get_system_prompt()}]

        # Add conversation history
        messages.extend(conversation_history)

        # Add current message
        messages.append({"role": "user", "content": current_message})

        return messages

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with the AI agent

        Args:
            user_id: User identifier (for tool calls)
            message: User's message content
            conversation_history: Previous messages in conversation (optional)
            tools: Available MCP tools for the agent (optional)

        Returns:
            {
                "response": "AI generated response",
                "tool_calls": [...],  # If any tools were invoked
                "finish_reason": "stop" | "tool_calls" | "length"
            }
        """
        conversation_history = conversation_history or []

        # Format messages for API
        messages = self.format_messages(conversation_history, message)

        logger.info(f"Processing message for user {user_id} with {len(messages)} messages in context")

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            # Extract response
            choice = response.choices[0]
            finish_reason = choice.finish_reason

            result = {
                "finish_reason": finish_reason
            }

            # Handle tool calls
            if finish_reason == "tool_calls" and choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                    for tc in choice.message.tool_calls
                ]
                result["response"] = choice.message.content or ""
            else:
                # Regular response
                result["response"] = choice.message.content

            logger.info(f"Agent processed message with finish_reason: {finish_reason}")
            return result

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            # Return user-friendly error message
            return {
                "response": "I'm experiencing high demand right now. Please try again in a moment.",
                "finish_reason": "error",
                "error": {
                    "type": "RateLimitError",
                    "message": "OpenAI API rate limit exceeded",
                    "user_message": "I'm experiencing high demand right now. Please try again in a moment."
                }
            }

        except AuthenticationError as e:
            logger.critical(f"OpenAI authentication failed: {str(e)}")
            # This is a configuration error - log critically
            return {
                "response": "I'm temporarily unavailable due to a configuration issue. Please contact support.",
                "finish_reason": "error",
                "error": {
                    "type": "AuthenticationError",
                    "message": "Invalid OpenAI API key",
                    "user_message": "Service configuration error. Please contact support."
                }
            }

        except APIConnectionError as e:
            logger.error(f"OpenAI API connection failed: {str(e)}")
            # Network/connection issue - suggest retry
            return {
                "response": "I'm having trouble connecting to my AI services. Please try again in a moment.",
                "finish_reason": "error",
                "error": {
                    "type": "ConnectionError",
                    "message": "Failed to connect to OpenAI API",
                    "user_message": "Connection error. Please try again shortly."
                }
            }

        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Server-side OpenAI error
            status_code = getattr(e, 'status_code', None)
            if status_code == 503:
                # Service unavailable
                return {
                    "response": "I'm temporarily unavailable. Please try again shortly.",
                    "finish_reason": "error",
                    "error": {
                        "type": "ServiceUnavailable",
                        "message": "OpenAI service temporarily unavailable",
                        "user_message": "Service temporarily unavailable. Please try again in a few minutes."
                    }
                }
            else:
                # Generic API error
                return {
                    "response": "I encountered an error processing your request. Please try again or rephrase your message.",
                    "finish_reason": "error",
                    "error": {
                        "type": "APIError",
                        "message": f"OpenAI API error: {str(e)}",
                        "user_message": "An error occurred. Please try again."
                    }
                }

        except OpenAIError as e:
            logger.error(f"OpenAI error: {str(e)}")
            # Catch-all for other OpenAI errors
            return {
                "response": "I encountered an unexpected error. Please try again.",
                "finish_reason": "error",
                "error": {
                    "type": "OpenAIError",
                    "message": f"OpenAI error: {str(e)}",
                    "user_message": "An unexpected error occurred. Please try again."
                }
            }

        except Exception as e:
            logger.error(f"Unexpected agent processing error: {str(e)}", exc_info=True)
            # Non-OpenAI error - log with full stack trace
            return {
                "response": "I encountered an unexpected error. Please try again.",
                "finish_reason": "error",
                "error": {
                    "type": "UnexpectedError",
                    "message": f"Unexpected error: {str(e)}",
                    "user_message": "An unexpected error occurred. Please try again."
                }
            }


    def truncate_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000
    ) -> List[Dict[str, str]]:
        """
        Truncate conversation history to fit within token limit

        Args:
            messages: List of messages
            max_tokens: Maximum tokens to keep (approximate)

        Returns:
            Truncated message list (keeps most recent messages)

        Note:
            This is a simple approximation. 1 token ≈ 4 characters.
            For production, use tiktoken for accurate token counting.
        """
        # Simple char-based approximation (4 chars per token)
        max_chars = max_tokens * 4
        total_chars = sum(len(msg["content"]) for msg in messages)

        if total_chars <= max_chars:
            return messages

        # Keep most recent messages
        truncated = []
        char_count = 0

        for msg in reversed(messages):
            msg_chars = len(msg["content"])
            if char_count + msg_chars > max_chars:
                break
            truncated.insert(0, msg)
            char_count += msg_chars

        logger.warning(f"Truncated history from {len(messages)} to {len(truncated)} messages")
        return truncated


# Global orchestrator instance
orchestrator = AgentOrchestrator()


def get_orchestrator() -> AgentOrchestrator:
    """
    Get the global agent orchestrator instance

    Returns:
        AgentOrchestrator: The configured orchestrator
    """
    return orchestrator


__all__ = ["AgentOrchestrator", "orchestrator", "get_orchestrator"]
