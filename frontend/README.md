# Todo AI Chatbot - Frontend

> **Version**: 1.0.0 | **Phase**: Production-Ready
> **Stack**: Next.js 15 + React 19 + OpenAI ChatKit + Better Auth

Modern conversational AI interface for task management built with Next.js 15, OpenAI ChatKit, and Better Auth. Features real-time chat, multi-turn conversations, and seamless authentication.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Development](#development)
- [Project Structure](#project-structure)
- [Authentication](#authentication)
- [API Integration](#api-integration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Features

### Core Capabilities
- **Conversational UI**: Natural language task management powered by OpenAI ChatKit
- **Multi-Turn Context**: Maintains conversation history for contextual understanding
- **Real-Time Chat**: Instant responses with streaming support (future feature)
- **User Authentication**: Secure JWT-based auth with Better Auth
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Task Management**: Create, view, complete, update, and delete tasks through chat

### User Experience
- **Clean Interface**: Minimal, distraction-free chat UI
- **Conversation History**: View and resume previous conversations
- **Error Handling**: Graceful error messages and recovery
- **Loading States**: Clear feedback during API calls
- **Accessibility**: ARIA labels and keyboard navigation support

---

## Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/) (App Router)
- **React**: [React 19](https://react.dev/)
- **UI Components**: [OpenAI ChatKit](https://github.com/openai/chatkit) for chat interface
- **Authentication**: [Better Auth](https://www.better-auth.com/) v1.0.0
- **Styling**: Tailwind CSS 3.x
- **Language**: TypeScript 5.7+
- **Package Manager**: npm or pnpm

---

## Quick Start

### Prerequisites
- **Node.js**: 18.18+ or 20.x (required for Next.js 15)
- **npm/pnpm**: Latest version
- **Backend API**: Running backend at http://localhost:8000 (see `backend/README.md`)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration (see Environment Configuration section)
   ```

4. **Run development server**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

5. **Open in browser**
   - Application: http://localhost:3000
   - Verify backend health: http://localhost:8000/health

---

## Environment Configuration

### Required Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
# Production: https://your-api.render.com or https://your-api.railway.app

# Better Auth Configuration
BETTER_AUTH_SECRET=your-secret-key-here-min-32-chars
# IMPORTANT: Must match BETTER_AUTH_SECRET in backend .env
# Generate with: openssl rand -base64 32

BETTER_AUTH_URL=http://localhost:3000
# Production: https://your-app.vercel.app
```

### Optional Variables

```bash
# OpenAI Configuration (if needed for client-side features)
# NEXT_PUBLIC_OPENAI_API_KEY=sk-...

# Analytics (optional)
# NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Feature Flags (optional)
# NEXT_PUBLIC_ENABLE_STREAMING=false
```

### Environment-Specific Configurations

**Development**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_URL=http://localhost:3000
```

**Production**:
```bash
NEXT_PUBLIC_API_URL=https://your-api.render.com
BETTER_AUTH_URL=https://your-app.vercel.app
```

**Important Notes**:
- All public environment variables must be prefixed with `NEXT_PUBLIC_`
- Never commit `.env.local` to version control (already in `.gitignore`)
- `BETTER_AUTH_SECRET` must match backend configuration exactly

---

## Development

### Running the Development Server

```bash
npm run dev
# or
pnpm dev
```

Server starts at http://localhost:3000 with:
- Hot Module Replacement (HMR)
- Fast Refresh for instant feedback
- TypeScript type checking
- ESLint warnings/errors

### Building for Production

```bash
npm run build
npm run start
```

This creates an optimized production build and starts the server.

### Linting

```bash
npm run lint
```

Runs ESLint with Next.js configuration to catch common issues.

### Type Checking

```bash
npx tsc --noEmit
```

Verifies TypeScript types without emitting files.

---

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── api/                    # API routes (Better Auth endpoints)
│   │   └── auth/               # Authentication routes
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home page with ChatInterface
│   └── globals.css             # Global styles (Tailwind)
│
├── components/                 # React components
│   └── ChatInterface.tsx       # Main chat UI (OpenAI ChatKit)
│
├── lib/                        # Utilities and configurations
│   ├── auth.ts                 # Better Auth client setup
│   └── api.ts                  # API client for backend
│
├── public/                     # Static assets
│   ├── favicon.ico
│   └── images/
│
├── .env.local.example          # Environment variable template
├── next.config.ts              # Next.js configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies and scripts
└── README.md                   # This file
```

### Key Files

#### `app/page.tsx`
Main page that renders the ChatInterface component. Handles routing and layout.

#### `components/ChatInterface.tsx`
OpenAI ChatKit integration for conversational AI. Manages:
- Chat message rendering
- User input
- API communication with backend
- Conversation state
- Error handling

#### `lib/auth.ts`
Better Auth client configuration:
- Session management
- JWT token handling
- User authentication state
- Protected route logic

#### `lib/api.ts`
Backend API client:
- HTTP request wrapper
- Authentication header injection
- Error handling
- Response parsing

---

## Authentication

### Better Auth Setup

Better Auth handles all authentication flows:
- **Sign Up**: Create new user account
- **Sign In**: Authenticate with credentials
- **Sign Out**: Clear session and JWT
- **Session Management**: Automatic token refresh
- **Protected Routes**: Middleware for auth-required pages

### Authentication Flow

1. **User signs in** → Better Auth validates credentials
2. **JWT token issued** → Stored in cookie (`better-auth.session_token`)
3. **Frontend requests** → Token automatically included in API calls
4. **Backend validates** → Verifies JWT signature and expiration
5. **User isolated** → All data filtered by `user_id` from JWT claims

### Implementing Protected Routes

```tsx
// app/chat/page.tsx
import { getSession } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function ChatPage() {
  const session = await getSession();

  if (!session) {
    redirect("/login");
  }

  return <ChatInterface userId={session.user.id} />;
}
```

### Session Management

```tsx
// Get current session
import { useSession } from "@/lib/auth";

function MyComponent() {
  const { session, loading } = useSession();

  if (loading) return <div>Loading...</div>;
  if (!session) return <div>Please sign in</div>;

  return <div>Welcome, {session.user.name}!</div>;
}
```

---

## API Integration

### Backend API Client

All API calls use the client from `lib/api.ts`:

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

async function apiCall(endpoint: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include', // Include cookies (JWT token)
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'API request failed');
  }

  return response.json();
}
```

### Making API Calls

```typescript
// Send chat message
const response = await apiCall(`/api/${userId}/chat`, {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    conversation_id: conversationId,
  }),
});

// Get conversations
const conversations = await apiCall(`/api/${userId}/conversations`);

// Delete conversation
await apiCall(`/api/${userId}/conversations/${conversationId}`, {
  method: 'DELETE',
});
```

### Error Handling

```typescript
try {
  const response = await apiCall('/api/user/chat', { ... });
  // Handle success
} catch (error) {
  if (error.message === 'Unauthorized') {
    // Redirect to login
  } else if (error.message.includes('Rate limit')) {
    // Show rate limit message
  } else {
    // Show generic error
  }
}
```

---

## Deployment

### Deployment Platforms

#### Vercel (Recommended)
1. Push code to GitHub repository
2. Import project at [vercel.com](https://vercel.com)
3. Configure environment variables in Vercel dashboard
4. Deploy automatically on every push to `main`

**Vercel Configuration**:
```json
{
  "buildCommand": "npm run build",
  "framework": "nextjs",
  "installCommand": "npm install"
}
```

#### Netlify
1. Create new site from Git
2. Set build command: `npm run build`
3. Set publish directory: `.next`
4. Configure environment variables
5. Deploy

#### Railway
1. Create new project from GitHub
2. Railway auto-detects Next.js
3. Add environment variables
4. Deploy

### Pre-Deployment Checklist

Before deploying to production:

- [ ] Set `NEXT_PUBLIC_API_URL` to production backend URL
- [ ] Set `BETTER_AUTH_URL` to production frontend URL
- [ ] Verify `BETTER_AUTH_SECRET` matches backend
- [ ] Configure CORS in backend to include production frontend URL
- [ ] Test authentication flow end-to-end
- [ ] Run `npm run build` locally to verify build succeeds
- [ ] Check for any environment variable references in code
- [ ] Verify API endpoints are accessible from production
- [ ] Test on mobile devices (responsive design)

### Environment Variables in Production

**Vercel/Netlify**:
- Add all variables from `.env.local` in dashboard
- Prefix public variables with `NEXT_PUBLIC_`
- Redeploy after changing environment variables

**Important**: Never expose sensitive keys (like `BETTER_AUTH_SECRET`) in `NEXT_PUBLIC_` variables!

---

## Troubleshooting

### Common Issues

#### "Failed to fetch" or CORS errors
```bash
# Check backend CORS configuration
# Ensure frontend URL is in CORS_ORIGINS environment variable in backend

# Verify backend is running
curl http://localhost:8000/health

# Check browser console for detailed CORS error
```

#### Authentication not working
```bash
# Verify BETTER_AUTH_SECRET matches between frontend and backend
# Check that cookies are enabled in browser
# Ensure credentials: 'include' is set in fetch calls
# Verify JWT token in browser cookies (Application tab → Cookies)
```

#### "Module not found" errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Restart dev server
npm run dev
```

#### Environment variables not working
```bash
# Verify variables are prefixed with NEXT_PUBLIC_ (for client-side access)
# Restart dev server after changing .env.local
# Check browser console: window.ENV to see available vars (in dev mode)
```

#### Build fails in production
```bash
# Run build locally to reproduce error
npm run build

# Check TypeScript errors
npx tsc --noEmit

# Check for missing environment variables
# Verify all imports resolve correctly
```

#### ChatKit not rendering
```bash
# Verify @openai/chatkit is installed
npm list @openai/chatkit

# Check browser console for errors
# Ensure backend API is accessible
# Verify NEXT_PUBLIC_API_URL is correct
```

### Debug Mode

Enable verbose logging:
```typescript
// lib/api.ts
const DEBUG = process.env.NODE_ENV === 'development';

async function apiCall(endpoint: string, options?: RequestInit) {
  if (DEBUG) {
    console.log('API Call:', endpoint, options);
  }

  // ... rest of implementation

  if (DEBUG) {
    console.log('API Response:', response);
  }
}
```

### Testing Locally

**Test with local backend**:
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**Test with production backend**:
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://your-api.render.com

npm run dev
```

---

## Development Tips

### Hot Reload
Next.js automatically reloads when you save files. If not working:
```bash
# Restart dev server
npm run dev
```

### Component Development
Use React DevTools browser extension to inspect component state and props.

### TypeScript Errors
Enable strict mode for better type safety:
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true
  }
}
```

### Performance
Monitor bundle size:
```bash
npm run build
# Check ".next/analyze" output
```

### Styling
Tailwind CSS utilities are auto-completed in VS Code with the Tailwind CSS IntelliSense extension.

---

## Scripts Reference

```bash
# Development
npm run dev          # Start dev server with hot reload

# Production
npm run build        # Build optimized production bundle
npm run start        # Start production server

# Quality
npm run lint         # Run ESLint
npx tsc --noEmit     # Type check without building
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test thoroughly
4. Ensure `npm run build` succeeds
5. Commit with descriptive messages
6. Push and create a Pull Request

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Next.js Docs](https://nextjs.org/docs)
- **OpenAI ChatKit**: [ChatKit Docs](https://github.com/openai/chatkit)
- **Better Auth**: [Better Auth Docs](https://www.better-auth.com/docs)

---

**Built with** ❤️ **using Next.js, React, and OpenAI ChatKit**
