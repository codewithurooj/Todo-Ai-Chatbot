/**
 * Better Auth configuration for authentication
 *
 * Provides JWT-based authentication with session management
 */

import { betterAuth } from "better-auth/client";

// Initialize Better Auth client
export const authClient = betterAuth({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",

  // JWT plugin configuration
  plugins: [],

  // Session configuration
  session: {
    cookieCache: {
      enabled: true,
      maxAge: 60 * 60 * 24 * 7, // 7 days
    },
  },
});

/**
 * Get the current user's session
 *
 * @returns Promise<Session | null>
 */
export async function getSession() {
  try {
    const session = await authClient.getSession();
    return session;
  } catch (error) {
    console.error("Failed to get session:", error);
    return null;
  }
}

/**
 * Get the current user's ID from session
 *
 * @returns Promise<string | null>
 */
export async function getUserId(): Promise<string | null> {
  const session = await getSession();
  return session?.user?.id || null;
}

/**
 * Get the authentication token for API calls
 *
 * @returns Promise<string | null>
 */
export async function getAuthToken(): Promise<string | null> {
  const session = await getSession();
  return session?.session?.token || null;
}

/**
 * Sign in with email and password
 *
 * @param email User email
 * @param password User password
 * @returns Promise<Session | null>
 */
export async function signIn(email: string, password: string) {
  try {
    const result = await authClient.signIn.email({
      email,
      password,
    });
    return result;
  } catch (error) {
    console.error("Sign in failed:", error);
    throw error;
  }
}

/**
 * Sign up with email and password
 *
 * @param email User email
 * @param password User password
 * @param name User name
 * @returns Promise<Session | null>
 */
export async function signUp(email: string, password: string, name?: string) {
  try {
    const result = await authClient.signUp.email({
      email,
      password,
      name,
    });
    return result;
  } catch (error) {
    console.error("Sign up failed:", error);
    throw error;
  }
}

/**
 * Sign out the current user
 */
export async function signOut() {
  try {
    await authClient.signOut();
  } catch (error) {
    console.error("Sign out failed:", error);
    throw error;
  }
}

export default authClient;
