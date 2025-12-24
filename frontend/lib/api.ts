/**
 * API client helper for backend communication
 *
 * Provides type-safe methods for calling the Todo AI Chatbot backend API
 */

import { getAuthToken, getUserId } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * API Error class for structured error handling
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Make an authenticated API request
 *
 * @param endpoint API endpoint (e.g., "/api/123/tasks")
 * @param options Fetch options
 * @returns Promise<Response>
 */
async function makeRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Add authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorCode = undefined;

    try {
      const errorData = await response.json();
      if (errorData.error) {
        errorMessage = errorData.error.message || errorMessage;
        errorCode = errorData.error.code;
      }
    } catch {
      // Failed to parse error JSON, use default message
    }

    throw new APIError(errorMessage, response.status, errorCode);
  }

  return response;
}

/**
 * Send a chat message to the AI assistant
 *
 * @param message User message
 * @param conversationId Optional conversation ID (creates new if not provided)
 * @returns Promise<ChatResponse>
 */
export async function sendChatMessage(
  message: string,
  conversationId?: number
): Promise<ChatResponse> {
  const userId = await getUserId();
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const response = await makeRequest(`/api/${userId}/chat`, {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  return response.json();
}

/**
 * Get list of user's conversations
 *
 * @param limit Maximum number of conversations to return
 * @param sortBy Sort field ("created_at" or "updated_at")
 * @param order Sort order ("asc" or "desc")
 * @returns Promise<Conversation[]>
 */
export async function getConversations(
  limit: number = 50,
  sortBy: "created_at" | "updated_at" = "updated_at",
  order: "asc" | "desc" = "desc"
): Promise<Conversation[]> {
  const userId = await getUserId();
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const params = new URLSearchParams({
    limit: limit.toString(),
    sort_by: sortBy,
    order,
  });

  const response = await makeRequest(
    `/api/${userId}/conversations?${params.toString()}`
  );

  return response.json();
}

/**
 * Get a specific conversation with messages
 *
 * @param conversationId Conversation ID
 * @returns Promise<ConversationWithMessages>
 */
export async function getConversation(
  conversationId: number
): Promise<ConversationWithMessages> {
  const userId = await getUserId();
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const response = await makeRequest(
    `/api/${userId}/conversations/${conversationId}`
  );

  return response.json();
}

/**
 * Delete a conversation
 *
 * @param conversationId Conversation ID
 * @returns Promise<void>
 */
export async function deleteConversation(
  conversationId: number
): Promise<void> {
  const userId = await getUserId();
  if (!userId) {
    throw new Error("User not authenticated");
  }

  await makeRequest(`/api/${userId}/conversations/${conversationId}`, {
    method: "DELETE",
  });
}

/**
 * Get all tasks for the user
 *
 * @returns Promise<Task[]>
 */
export async function getTasks(): Promise<Task[]> {
  const userId = await getUserId();
  if (!userId) {
    throw new Error("User not authenticated");
  }

  const response = await makeRequest(`/api/${userId}/tasks`);
  return response.json();
}

/**
 * Health check
 *
 * @returns Promise<HealthCheck>
 */
export async function healthCheck(): Promise<HealthCheck> {
  const response = await makeRequest("/health");
  return response.json();
}

// Type definitions

export interface ChatResponse {
  conversation_id: number;
  response: string;
  tool_calls?: ToolCall[];
  created_at: string;
}

export interface ToolCall {
  tool: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface Conversation {
  id: number;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface Task {
  id: number;
  user_id: string;
  title: string;
  description?: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  components: {
    api: string;
    database: string;
    openai: string;
  };
  version: string;
}
