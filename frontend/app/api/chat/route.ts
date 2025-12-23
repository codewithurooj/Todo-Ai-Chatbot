/**
 * API route proxy for chat endpoint
 *
 * This proxies requests to the backend API, allowing us to:
 * - Keep backend URL configuration server-side
 * - Add request/response transformation if needed
 * - Implement rate limiting or caching
 */

import { NextRequest, NextResponse } from "next/server";
import { getAuthToken, getUserId } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Get user authentication
    const token = await getAuthToken();
    const userId = await getUserId();

    if (!token || !userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await request.json();

    // Forward request to backend
    const response = await fetch(`${API_BASE_URL}/api/${userId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    // Parse backend response
    const data = await response.json();

    // Return response with appropriate status
    if (!response.ok) {
      return NextResponse.json(
        data,
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json(
    { message: "Chat API - Use POST to send messages" },
    { status: 405 }
  );
}
