# Quick

start: AI-Powered Todo Chatbot Implementation

## Prerequisites

- Python 3.13+ installed
- Node.js 18+ installed (for frontend)
- UV package manager installed (`pip install uv`)
- PostgreSQL client (psql) for database verification
- Git configured
- OpenAI API key
- Neon PostgreSQL database created

---

## Environment Setup

### Backend Environment

**File**: `backend/.env`

```bash
# Database
DATABASE_URL=postgresql://user:password@neon.tech:5432/dbname

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# Better Auth
BETTER_AUTH_SECRET=your-secret-key-here

# MCP Server
MCP_SERVER_URL=http://localhost:8001

# Agent Configuration
MAX_CONVERSATION_HISTORY=20
MAX_TOOL_CALLS_PER_REQUEST=5
```

### Frontend Environment

**File**: `frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
BETTER_AUTH_SECRET=your-secret-key-here  # Same as backend
```

---

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Run migrations
alembic upgrade head
```

### 3. Verify Database

```bash
# Connect to Neon PostgreSQL
psql $DATABASE_URL

# Verify tables exist
\dt

# Expected tables:
# - users
# - tasks
# - conversations
# - messages
```

### 4. Start Backend Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Start MCP Server (Separate Process)

```bash
# In new terminal
cd backend
source .venv/bin/activate
python app/mcp/server.py
```

**Verify Backend**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","services":{...}}
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Better Auth

```bash
# Install Better Auth
npm install better-auth @better-auth/next

# Configure in lib/auth.ts (see spec for details)
```

### 3. Start Development Server

```bash
npm run dev
```

**Verify Frontend**:
- Open http://localhost:3000
- Should see login/signup page

---

## Testing Strategy

### Backend Unit Tests

```bash
cd backend
pytest tests/unit/ -v

# Test specific module
pytest tests/unit/test_mcp_tools.py -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
```

### Backend Integration Tests

```bash
pytest tests/integration/ -v

# Test specific endpoint
pytest tests/integration/test_chat_endpoint.py -v
```

### End-to-End Tests

```bash
pytest tests/e2e/test_user_scenarios.py -v
```

### Frontend Tests

```bash
cd frontend
npm test

# With coverage
npm test -- --coverage
```

---

## Development Workflow

### 1. Database Changes

```bash
# Edit SQLModel schema in app/models/

# Generate migration
alembic revision --autogenerate -m "Add new field"

# Review migration file in migrations/versions/

# Run migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 2. Adding New MCP Tool

```bash
# 1. Define tool in app/mcp/tools/new_tool.py
# 2. Register tool in app/mcp/server.py
# 3. Write unit tests in tests/unit/test_mcp_tools.py
# 4. Update contracts/mcp-tools.md documentation
# 5. Update agent system prompt if needed
```

### 3. Adding New API Endpoint

```bash
# 1. Define route in app/routes/new_endpoint.py
# 2. Add JWT middleware if needed
# 3. Write integration tests
# 4. Update contracts/api-endpoints.md documentation
```

### 4. Modifying Agent Behavior

```bash
# 1. Edit system prompt in app/agent/system_prompt.py
# 2. Test with various user messages
# 3. Run E2E tests to verify no regressions
```

---

## Common Tasks

### Reset Database (Development Only)

```bash
# Drop all tables
alembic downgrade base

# Recreate all tables
alembic upgrade head
```

### View Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# MCP server logs
tail -f backend/logs/mcp.log
```

### Debug OpenAI Agent

```bash
# Enable debug logging
export ENABLE_DEBUG_LOGGING=true

# Run backend
uvicorn app.main:app --reload --log-level debug
```

### Test Chat Endpoint

```bash
# Get JWT token (via Better Auth login first)
TOKEN="your-jwt-token"

# Send chat message
curl -X POST http://localhost:8000/api/123/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "add task to buy groceries"}'
```

---

## Deployment Checklist

### Backend Deployment

- [ ] Set production DATABASE_URL
- [ ] Set OPENAI_API_KEY
- [ ] Set BETTER_AUTH_SECRET (same as frontend)
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Set environment variables in hosting platform
- [ ] Configure CORS for production frontend domain
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging
- [ ] Configure rate limiting

### Frontend Deployment (Vercel)

- [ ] Set NEXT_PUBLIC_API_URL to production backend URL
- [ ] Set BETTER_AUTH_SECRET (same as backend)
- [ ] Configure OpenAI domain allowlist (required for ChatKit)
- [ ] Add production domain to Better Auth allowed origins
- [ ] Enable automatic deployments from Git
- [ ] Configure environment variables in Vercel dashboard

---

## Troubleshooting

### Database Connection Error

```bash
# Test connection
psql $DATABASE_URL

# If fails, check:
# 1. DATABASE_URL format: postgresql://user:pass@host:5432/dbname
# 2. Neon instance is running
# 3. Network/firewall allows connections
```

### OpenAI API Error

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# If fails, check:
# 1. API key is valid (starts with sk-proj- or sk-)
# 2. API key has correct permissions
# 3. Account has credits
```

### MCP Server Not Responding

```bash
# Check if running
curl http://localhost:8001/health

# Check logs
tail -f backend/logs/mcp.log

# Restart MCP server
pkill -f "python app/mcp/server.py"
python app/mcp/server.py
```

### JWT Validation Failing

```bash
# Verify JWT secret matches between frontend and backend
# Check .env files

# Test JWT manually
python -c "import jwt; print(jwt.decode('token', 'secret', algorithms=['HS256']))"
```

---

## Performance Optimization

### Database

```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Analyze query plan
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 123 AND completed = false;

# Ensure indexes exist
\di
```

### Backend

```bash
# Profile endpoint performance
python -m cProfile -o profile.stats app/main.py

# Analyze profile
python -m pstats profile.stats
```

### Frontend

```bash
# Build optimization
npm run build

# Analyze bundle size
npm run analyze
```

---

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
psql $DATABASE_URL -c "SELECT 1;"

# OpenAI API health
curl https://status.openai.com/api/v2/status.json
```

### Metrics to Monitor

- Chat endpoint response time (p95 < 3s)
- Database query time (p95 < 500ms)
- Error rate (< 1%)
- OpenAI API failures
- MCP tool execution time
- Rate limit violations

---

## Next Steps

1. **Run Tests**: Ensure all tests pass before deployment
2. **Load Test**: Test with 100 concurrent users
3. **Security Audit**: Review authentication, authorization, input validation
4. **Documentation**: Update README.md with deployment instructions
5. **Deploy**: Follow deployment checklist above

---

**This quickstart provides essential commands and workflows for developing and deploying the Todo AI Chatbot. Refer to the full specifications in `plan.md`, `data-model.md`, and `contracts/` for detailed design decisions.**
