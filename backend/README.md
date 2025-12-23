# Todo AI Chatbot - Backend API

> **Version**: 3.0.0 | **Phase**: Production-Ready Phase 9
> **Stack**: FastAPI + PostgreSQL + OpenAI Agents SDK + MCP Tools

AI-powered conversational task management API built with FastAPI, OpenAI's Agents SDK, and Model Context Protocol (MCP) tools. Features multi-turn conversations, intelligent intent detection, and complete task CRUD operations through natural language.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Security](#security)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Features

### Core Capabilities
- **Conversational AI**: Natural language task management using OpenAI GPT-4o
- **Multi-Turn Context**: Maintains conversation history for contextual understanding
- **MCP Tool Integration**: Modular task operations (add, list, complete, update, delete)
- **User Isolation**: JWT-based authentication with strict data isolation
- **Rate Limiting**: 100 requests/hour, 20 requests/minute per user
- **Input Validation**: Comprehensive request validation and sanitization
- **Error Handling**: Structured error responses with user-friendly messages

### Technical Highlights
- **Stateless Architecture**: Every request is independent, scales horizontally
- **Database-First**: PostgreSQL (Neon) as source of truth for all state
- **Production-Ready**: Request logging, error tracking, CORS configuration
- **Type-Safe**: Full Pydantic validation for requests and responses
- **OpenAPI Docs**: Auto-generated interactive API documentation

---

## Architecture

### Stack
- **Web Framework**: FastAPI 0.115+
- **Database**: PostgreSQL (Neon serverless)
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **AI Agent**: OpenAI Agents SDK with GPT-4o
- **Authentication**: Better Auth (JWT tokens)
- **Tools Protocol**: Model Context Protocol (MCP)

### Key Components

```
backend/
├── app/
│   ├── main.py                  # FastAPI app initialization, CORS, middleware
│   ├── config.py                # Environment configuration (Pydantic Settings)
│   ├── database.py              # Database engine, session management
│   │
│   ├── routes/                  # API endpoints
│   │   ├── health.py            # Health check endpoint
│   │   ├── tasks.py             # Task CRUD endpoints
│   │   ├── chat.py              # Conversational AI endpoint
│   │   └── conversations.py     # Conversation management endpoints
│   │
│   ├── models/                  # SQLModel database models
│   │   ├── task.py              # Task model and schemas
│   │   ├── conversation.py      # Conversation model
│   │   └── message.py           # Message model
│   │
│   ├── agent/                   # AI agent orchestration
│   │   ├── orchestrator.py      # OpenAI agent coordinator
│   │   ├── conversation_manager.py  # Message storage and retrieval
│   │   └── system_prompt.py     # Agent system prompt template
│   │
│   ├── mcp/                     # Model Context Protocol tools
│   │   ├── server.py            # MCP tool registration
│   │   └── tools/               # Individual MCP tools
│   │       ├── add_task.py      # Create new task
│   │       ├── list_tasks.py    # Retrieve tasks with filtering
│   │       ├── complete_task.py # Mark task as completed
│   │       ├── update_task.py   # Update task details
│   │       └── delete_task.py   # Delete task
│   │
│   └── middleware/              # Request/response middleware
│       ├── auth.py              # JWT validation, rate limiting
│       ├── error_handler.py     # Global error handling
│       └── logging.py           # Request logging with request_id
│
├── migrations/                  # Alembic database migrations
├── tests/                       # Test suite (pytest)
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Quick Start

### Prerequisites
- **Python**: 3.11 or higher
- **PostgreSQL**: 14+ (or Neon serverless account)
- **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)
- **Better Auth**: Configured frontend authentication

### Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Environment Configuration section)
   ```

5. **Initialize database**
   ```bash
   # Run migrations to create tables
   alembic upgrade head
   ```

6. **Run development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Verify installation**
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## Environment Configuration

### Required Variables

Create a `.env` file in the `backend/` directory with the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/database
# Example (Neon): postgresql://user:password@ep-cool-name-12345.us-east-1.aws.neon.tech/neondb?sslmode=require

# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-...
# Get your API key from: https://platform.openai.com/api-keys

# Authentication Configuration
BETTER_AUTH_SECRET=your-secret-key-here-min-32-chars
# Must match the secret used in your Better Auth frontend configuration

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
# Production: Replace with your frontend URL (e.g., https://your-app.vercel.app)
# IMPORTANT: Wildcards (*.vercel.app) are NOT supported - specify each origin explicitly
```

### Optional Variables

```bash
# Application Configuration
ENVIRONMENT=development           # "development" or "production"
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false                      # Enable debug mode (auto-reload, verbose logs)

# OpenAI Model Configuration
OPENAI_MODEL=gpt-4o-mini         # or "gpt-4o" for higher quality (more expensive)

# Better Auth URL (optional)
BETTER_AUTH_URL=http://localhost:3000/api/auth

# Rate Limiting (optional)
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_MINUTE=20

# API Settings
API_V1_PREFIX=/api
PROJECT_NAME=Todo AI Chatbot API
PROJECT_VERSION=3.0.0
```

### Environment-Specific Configurations

**Development**:
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
OPENAI_MODEL=gpt-4o-mini  # Cost-effective for development
```

**Production**:
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
CORS_ORIGINS=https://your-app.vercel.app
OPENAI_MODEL=gpt-4o  # Higher quality for production
```

---

## Development

### Running the Server

**Development mode** (auto-reload on code changes):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Migrations

**Create a new migration**:
```bash
alembic revision --autogenerate -m "description of changes"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback migration**:
```bash
alembic downgrade -1
```

### Testing

**Run all tests**:
```bash
pytest
```

**Run with coverage**:
```bash
pytest --cov=app --cov-report=html
```

**Run specific test file**:
```bash
pytest tests/test_chat.py -v
```

### Code Quality

**Format code**:
```bash
black app/
isort app/
```

**Linting**:
```bash
flake8 app/
mypy app/
```

---

## API Documentation

### Interactive API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Health Check
```
GET /health
```
Returns API health status and version information.

#### Chat (Conversational AI)
```
POST /api/{user_id}/chat
Authorization: Bearer <jwt_token>

Request:
{
  "message": "add task to buy groceries",
  "conversation_id": 123  // optional, creates new if not provided
}

Response:
{
  "conversation_id": 123,
  "response": "I've added 'Buy groceries' to your task list.",
  "tool_calls": [
    {"tool": "add_task", "result": {"task_id": 456, "title": "Buy groceries"}}
  ],
  "created_at": "2025-12-21T10:30:05Z"
}
```

#### List Conversations
```
GET /api/{user_id}/conversations
Authorization: Bearer <jwt_token>

Response:
[
  {
    "id": 123,
    "user_id": "user-456",
    "created_at": "2025-12-21T10:00:00Z",
    "updated_at": "2025-12-21T10:30:00Z"
  }
]
```

#### Get Conversation Messages
```
GET /api/{user_id}/conversations/{conversation_id}/messages
Authorization: Bearer <jwt_token>

Response:
[
  {
    "id": 1,
    "conversation_id": 123,
    "user_id": "user-456",
    "role": "user",
    "content": "add task to buy groceries",
    "created_at": "2025-12-21T10:30:00Z"
  },
  {
    "id": 2,
    "conversation_id": 123,
    "user_id": "user-456",
    "role": "assistant",
    "content": "I've added 'Buy groceries' to your task list.",
    "created_at": "2025-12-21T10:30:05Z"
  }
]
```

#### Delete Conversation
```
DELETE /api/{user_id}/conversations/{conversation_id}
Authorization: Bearer <jwt_token>

Response:
{
  "success": true,
  "deleted_conversation_id": 123,
  "deleted_message_count": 10,
  "message": "Conversation and messages deleted successfully"
}
```

### Error Responses

All errors follow this format:
```json
{
  "error": "ErrorType",
  "message": "User-friendly error message",
  "retry_after": 60  // Only for rate limiting (429)
}
```

**Error Types**:
- `ValidationError` (400): Invalid request parameters
- `Unauthorized` (401): Missing or invalid authentication
- `Forbidden` (403): Access denied (e.g., accessing other user's data)
- `NotFound` (404): Resource not found
- `RateLimitExceeded` (429): Too many requests
- `InternalServerError` (500): Server error

---

## Database

### Schema

**conversations**:
- `id` (int, primary key)
- `user_id` (str, indexed)
- `created_at` (datetime)
- `updated_at` (datetime)

**messages**:
- `id` (int, primary key)
- `conversation_id` (int, foreign key, indexed)
- `user_id` (str, indexed)
- `role` (str: "user" or "assistant")
- `content` (str, max 10000 chars)
- `created_at` (datetime)

**tasks**:
- `id` (int, primary key)
- `user_id` (str, indexed)
- `title` (str, 1-200 chars)
- `description` (str, optional)
- `completed` (bool, default: false)
- `created_at` (datetime)
- `updated_at` (datetime)

### Index Optimization

Current indexes provide adequate performance for small-medium scale deployments. For production optimization, see `DATABASE_INDEXES.md` for recommended composite indexes.

**Existing indexes**:
- `conversations.user_id`
- `messages.conversation_id`
- `messages.user_id`
- `tasks.user_id`

**Recommended composite indexes** (for scale):
- `tasks(user_id, completed, created_at)` - for filtered task lists
- `conversations(user_id, updated_at)` - for sorting conversations
- `messages(conversation_id, created_at)` - for message history

See `DATABASE_INDEXES.md` for detailed migration instructions.

---

## Security

### Authentication
- **JWT Validation**: All endpoints (except `/health`) require valid JWT token
- **Token Sources**: Authorization header (`Bearer <token>`) or `better-auth.session_token` cookie
- **User Isolation**: All queries filter by `user_id` from JWT claims
- **Token Verification**: Signature validated using `BETTER_AUTH_SECRET`

### Input Validation
- **Message Length**: 1-10,000 characters
- **HTML Escaping**: Prevents XSS attacks
- **Null Byte Check**: Prevents injection attacks
- **Pydantic Validation**: Type-safe request schemas

### Rate Limiting
- **Per User**: 100 requests/hour, 20 requests/minute
- **Enforcement**: JWT-based user identification
- **Response**: 429 status with `retry_after` seconds

### CORS Configuration
- **Development**: `http://localhost:3000`, `http://localhost:3001`
- **Production**: Configure via `CORS_ORIGINS` environment variable
- **Important**: Wildcards not supported - specify each origin explicitly

### Data Isolation
- **Strict Filtering**: All database queries include `user_id` filter
- **No Cross-User Access**: Users can only access their own data
- **Conversation Ownership**: Verified on every request

---

## Deployment

### Environment Checklist

Before deploying to production:

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure production `DATABASE_URL` (Neon recommended)
- [ ] Set secure `BETTER_AUTH_SECRET` (min 32 characters)
- [ ] Configure `CORS_ORIGINS` with production frontend URL
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Verify `OPENAI_API_KEY` is valid and has sufficient credits
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Test health endpoint: `/health`

### Deployment Platforms

#### Render (Recommended)
1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Deploy

#### Railway
1. Create new project from GitHub
2. Configure environment variables
3. Railway auto-detects Python and installs dependencies
4. Set start command in `Procfile` or railway.toml
5. Deploy

#### Vercel (Serverless)
1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json` with configuration
3. Run `vercel` to deploy
4. Configure environment variables in Vercel dashboard

### Database (Neon)
1. Create Neon project at [neon.tech](https://neon.tech)
2. Copy connection string
3. Set `DATABASE_URL` environment variable
4. Run migrations: `alembic upgrade head`

### Monitoring
- **Health Checks**: `/health` endpoint for uptime monitoring
- **Logs**: Structured logging with request_id for traceability
- **Error Tracking**: All errors logged with full stack traces
- **Rate Limiting**: Monitor 429 responses for abuse

---

## Troubleshooting

### Common Issues

#### "No module named 'app'"
```bash
# Ensure you're in the backend/ directory
cd backend

# Verify Python environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### "Connection to database failed"
```bash
# Check DATABASE_URL in .env
echo $DATABASE_URL

# Test connection manually
psql "$DATABASE_URL"

# Verify Neon database is running (if using Neon)
```

#### "Invalid authentication credentials"
```bash
# Verify BETTER_AUTH_SECRET matches frontend configuration
# Check JWT token is being sent in Authorization header or cookie
# Ensure token hasn't expired
```

#### "CORS policy error"
```bash
# Verify frontend URL is in CORS_ORIGINS
# Check for trailing slashes (http://localhost:3000 vs http://localhost:3000/)
# Ensure credentials are enabled in frontend fetch calls
```

#### "OpenAI API error"
```bash
# Verify OPENAI_API_KEY is set correctly
# Check API key has sufficient credits
# Verify model name (gpt-4o-mini or gpt-4o)
# Check OpenAI API status: https://status.openai.com
```

#### "Rate limit exceeded"
```bash
# User has exceeded 100 requests/hour or 20 requests/minute
# Check rate limit configuration in .env
# Wait for retry_after seconds (returned in 429 response)
```

### Debug Mode

Enable verbose logging:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug
```

### Database Issues

**Reset database** (⚠️ destroys all data):
```bash
# Downgrade all migrations
alembic downgrade base

# Re-apply migrations
alembic upgrade head
```

**View migration history**:
```bash
alembic history
alembic current
```

### Performance Issues

**Check database query performance**:
```bash
# Enable SQL logging
DEBUG=true
# Queries will be logged to console
```

**Monitor request times**:
```bash
# Check request_id in logs
# Correlate slow requests with database queries
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test thoroughly
4. Commit with descriptive messages
5. Push and create a Pull Request

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Project Wiki](https://github.com/your-repo/wiki)
- **API Docs**: http://localhost:8000/docs (when running locally)

---

**Built with** ❤️ **using FastAPI, OpenAI, and PostgreSQL**
