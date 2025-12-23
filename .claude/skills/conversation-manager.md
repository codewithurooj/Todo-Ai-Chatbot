# Conversation Manager Skill

## Purpose
Manage chat conversation lifecycle, message storage, and conversation history retrieval for the stateless AI chatbot. This skill handles all conversation-related database operations following the Phase III architecture.

## Capabilities
- Create new conversations for users
- Retrieve conversation history with full message context
- Store user and assistant messages
- List user's conversations
- Update conversation activity timestamps
- Enforce user isolation (users can only access their own conversations)
- Handle conversation pagination and sorting

## Core Responsibilities

### 1. Conversation Creation
Create new conversation records when users start fresh chat sessions.

**Behavior:**
- Generate unique conversation ID
- Associate conversation with user_id
- Set created_at and updated_at timestamps
- Return conversation metadata

**Input:**
```typescript
{
  user_id: string;
}
```

**Output:**
```typescript
{
  conversation_id: number;
  user_id: string;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}
```

### 2. Message Storage
Store user messages and AI assistant responses in conversations.

**Behavior:**
- Validate conversation exists and belongs to user
- Store message with role (user/assistant), content, timestamp
- Update conversation's updated_at timestamp
- Enforce message length limits (10,000 characters)
- Return stored message metadata

**Input:**
```typescript
{
  conversation_id: number;
  user_id: string;
  role: "user" | "assistant";
  content: string;
}
```

**Output:**
```typescript
{
  message_id: number;
  conversation_id: number;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string; // ISO 8601
}
```

### 3. Conversation History Retrieval
Fetch complete message history for a conversation to provide AI context.

**Behavior:**
- Validate user owns the conversation (user isolation)
- Retrieve all messages ordered chronologically
- Return messages with role and content
- Support pagination for very long conversations

**Input:**
```typescript
{
  conversation_id: number;
  user_id: string;
  limit?: number; // default: all messages
  offset?: number; // default: 0
}
```

**Output:**
```typescript
{
  conversation_id: number;
  user_id: string;
  messages: [
    {
      message_id: number;
      role: "user" | "assistant";
      content: string;
      created_at: string;
    }
  ],
  total_messages: number;
  has_more: boolean;
}
```

### 4. List User Conversations
Retrieve all conversations for a user with metadata and sorting options.

**Behavior:**
- Return all conversations owned by user_id
- Support sorting (by created_at or updated_at)
- Support ordering (ascending or descending)
- Support pagination
- Include message count for each conversation

**Input:**
```typescript
{
  user_id: string;
  sort_by?: "created_at" | "updated_at"; // default: updated_at
  order?: "asc" | "desc"; // default: desc
  limit?: number; // default: 50
  offset?: number; // default: 0
}
```

**Output:**
```typescript
{
  conversations: [
    {
      conversation_id: number;
      user_id: string;
      created_at: string;
      updated_at: string;
      message_count: number;
      last_message_preview?: string; // Optional: first 100 chars
    }
  ],
  total_conversations: number;
  has_more: boolean;
}
```

### 5. Delete Conversation
Remove a conversation and all its messages (cascade delete).

**Behavior:**
- Validate user owns the conversation
- Delete all messages in the conversation
- Delete conversation record
- Return success confirmation

**Input:**
```typescript
{
  conversation_id: number;
  user_id: string;
}
```

**Output:**
```typescript
{
  success: boolean;
  deleted_conversation_id: number;
  deleted_message_count: number;
}
```

### 6. Get Conversation Metadata
Retrieve conversation details without messages (lightweight query).

**Behavior:**
- Validate user owns conversation
- Return conversation metadata only
- Include message count

**Input:**
```typescript
{
  conversation_id: number;
  user_id: string;
}
```

**Output:**
```typescript
{
  conversation_id: number;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}
```

## Security & Validation

### User Isolation Enforcement
**CRITICAL:** Every operation MUST verify user_id matches the conversation owner.

```python
# Conceptual validation
def validate_user_owns_conversation(conversation_id, user_id):
    conversation = db.get_conversation(conversation_id)
    if conversation is None:
        raise ConversationNotFoundError()
    if conversation.user_id != user_id:
        raise UnauthorizedAccessError("Cannot access other users' conversations")
    return conversation
```

### Input Validation
- **user_id:** Required, non-empty string
- **conversation_id:** Required, positive integer
- **role:** Must be exactly "user" or "assistant"
- **content:** Required, 1-10,000 characters
- **limit:** Optional, 1-1000 (prevent excessive queries)
- **offset:** Optional, non-negative integer

### Error Handling
```typescript
// Error types to handle
{
  ConversationNotFoundError: {
    status: 404,
    message: "Conversation not found"
  },
  UnauthorizedAccessError: {
    status: 403,
    message: "Cannot access this conversation"
  },
  ValidationError: {
    status: 400,
    message: "Invalid input parameters"
  },
  MessageTooLongError: {
    status: 400,
    message: "Message exceeds 10,000 character limit"
  },
  DatabaseError: {
    status: 500,
    message: "Database operation failed"
  }
}
```

## Usage Examples

### Example 1: Start New Conversation
```typescript
// User sends first message
const user_id = "user_123";
const message = "I need to add a task";

// Step 1: Create conversation
const conversation = await conversation_manager.create_conversation({
  user_id: user_id
});
// Returns: { conversation_id: 456, user_id: "user_123", ... }

// Step 2: Store user message
await conversation_manager.store_message({
  conversation_id: 456,
  user_id: user_id,
  role: "user",
  content: message
});

// Step 3: (After AI processes) Store assistant response
await conversation_manager.store_message({
  conversation_id: 456,
  user_id: user_id,
  role: "assistant",
  content: "I've added that task for you!"
});
```

### Example 2: Continue Existing Conversation
```typescript
// User sends another message in conversation 456
const user_id = "user_123";
const conversation_id = 456;
const new_message = "Show me my tasks";

// Step 1: Retrieve conversation history for AI context
const history = await conversation_manager.get_conversation_history({
  conversation_id: conversation_id,
  user_id: user_id
});
// Returns all previous messages

// Step 2: Store new user message
await conversation_manager.store_message({
  conversation_id: conversation_id,
  user_id: user_id,
  role: "user",
  content: new_message
});

// Step 3: AI processes with history context, then store response
await conversation_manager.store_message({
  conversation_id: conversation_id,
  user_id: user_id,
  role: "assistant",
  content: "Here are your tasks: ..."
});
```

### Example 3: List User's Conversations
```typescript
// User wants to see all their conversations
const user_id = "user_123";

const conversations = await conversation_manager.list_conversations({
  user_id: user_id,
  sort_by: "updated_at",
  order: "desc",
  limit: 20
});

// Returns conversations sorted by most recently active
// [
//   { conversation_id: 789, updated_at: "2025-12-19 15:30", ... },
//   { conversation_id: 456, updated_at: "2025-12-19 10:00", ... },
//   ...
// ]
```

### Example 4: Delete Old Conversation
```typescript
// User wants to delete conversation 123
const user_id = "user_123";
const conversation_id = 123;

const result = await conversation_manager.delete_conversation({
  conversation_id: conversation_id,
  user_id: user_id
});

// Returns: { success: true, deleted_conversation_id: 123, deleted_message_count: 45 }
```

## Integration with Other Components

### With OpenAI Agent Orchestrator
The orchestrator uses conversation_manager to:
1. Retrieve conversation history before AI processing
2. Store user messages when received
3. Store AI responses after generation

```typescript
// Orchestrator flow
async function process_chat_message(user_id, conversation_id, message) {
  // Get context
  const history = await conversation_manager.get_conversation_history({
    conversation_id,
    user_id
  });

  // Store user message
  await conversation_manager.store_message({
    conversation_id,
    user_id,
    role: "user",
    content: message
  });

  // Process with AI (using history for context)
  const ai_response = await ai_agent.process(message, history);

  // Store AI response
  await conversation_manager.store_message({
    conversation_id,
    user_id,
    role: "assistant",
    content: ai_response
  });

  return ai_response;
}
```

### With Stateless API
API endpoints delegate to conversation_manager:

```typescript
// POST /api/{user_id}/chat
app.post('/api/:user_id/chat', async (req, res) => {
  const { user_id } = req.params;
  const { conversation_id, message } = req.body;

  let conv_id = conversation_id;

  // Create new conversation if none provided
  if (!conv_id) {
    const conversation = await conversation_manager.create_conversation({
      user_id
    });
    conv_id = conversation.conversation_id;
  }

  // Process message using orchestrator (which uses conversation_manager)
  const response = await orchestrator.process_chat_message(
    user_id,
    conv_id,
    message
  );

  res.json({ conversation_id: conv_id, response });
});

// GET /api/{user_id}/conversations
app.get('/api/:user_id/conversations', async (req, res) => {
  const { user_id } = req.params;
  const { limit, sort, order } = req.query;

  const conversations = await conversation_manager.list_conversations({
    user_id,
    sort_by: sort || "updated_at",
    order: order || "desc",
    limit: parseInt(limit) || 50
  });

  res.json(conversations);
});
```

## Database Operations

### Tables Used
- **conversations** - Conversation metadata
- **messages** - Individual messages within conversations

### Key Queries

#### Create Conversation
```sql
-- Conceptual SQL
INSERT INTO conversations (user_id, created_at, updated_at)
VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
RETURNING id, user_id, created_at, updated_at;
```

#### Store Message
```sql
-- Conceptual SQL
-- Step 1: Insert message
INSERT INTO messages (conversation_id, user_id, role, content, created_at)
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
RETURNING id, conversation_id, user_id, role, content, created_at;

-- Step 2: Update conversation timestamp
UPDATE conversations
SET updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
```

#### Get Conversation History
```sql
-- Conceptual SQL
SELECT m.id, m.role, m.content, m.created_at
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
WHERE c.id = ? AND c.user_id = ?
ORDER BY m.created_at ASC
LIMIT ? OFFSET ?;
```

#### List Conversations
```sql
-- Conceptual SQL
SELECT
  c.id,
  c.user_id,
  c.created_at,
  c.updated_at,
  COUNT(m.id) as message_count
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE c.user_id = ?
GROUP BY c.id
ORDER BY c.updated_at DESC
LIMIT ? OFFSET ?;
```

## Performance Considerations

### Indexing Strategy
```sql
-- Conceptual indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### Query Optimization
- **Pagination:** Always use LIMIT/OFFSET to prevent full table scans
- **Conversation History:** For very long conversations (1000+ messages), consider limiting history sent to AI (e.g., last 100 messages)
- **List Operations:** Use COUNT with proper indexes for message counts
- **Caching:** Consider caching recent conversation metadata (if using Redis)

### Scalability
- **Horizontal Scaling:** Stateless design allows multiple instances
- **Database:** Use connection pooling, read replicas for heavy load
- **Archival:** Consider moving old conversations (90+ days) to archive storage

## Testing Strategy

### Unit Tests
```python
# Conceptual test cases
def test_create_conversation_returns_valid_metadata():
    result = conversation_manager.create_conversation(user_id="test_123")
    assert result.conversation_id > 0
    assert result.user_id == "test_123"
    assert result.created_at is not None

def test_store_message_validates_user_ownership():
    # User tries to add message to another user's conversation
    with pytest.raises(UnauthorizedAccessError):
        conversation_manager.store_message(
            conversation_id=456,  # Owned by user_123
            user_id="user_999",   # Different user
            role="user",
            content="test"
        )

def test_get_history_returns_chronological_messages():
    # Setup: Create conversation with 5 messages
    # Test: Retrieve history
    history = conversation_manager.get_conversation_history(
        conversation_id=456,
        user_id="test_123"
    )
    assert len(history.messages) == 5
    assert history.messages[0].created_at < history.messages[4].created_at
```

### Integration Tests
```python
# Conceptual integration tests
def test_full_conversation_flow():
    # Create conversation
    conv = create_conversation(user_id="test_123")

    # Store user message
    store_message(conv.id, "test_123", "user", "Hello")

    # Store assistant message
    store_message(conv.id, "test_123", "assistant", "Hi there!")

    # Retrieve history
    history = get_conversation_history(conv.id, "test_123")
    assert len(history.messages) == 2
    assert history.messages[0].role == "user"
    assert history.messages[1].role == "assistant"
```

## Error Recovery

### Transaction Handling
```python
# Conceptual transaction pattern
async def store_message_with_timestamp_update(conversation_id, user_id, role, content):
    async with db.transaction():
        # Both operations succeed or both fail
        message = await db.insert_message(conversation_id, user_id, role, content)
        await db.update_conversation_timestamp(conversation_id)
        return message
```

### Graceful Degradation
- If conversation history retrieval fails, allow message storage to proceed
- If timestamp update fails, log error but don't block message storage
- Provide partial results when possible (e.g., return available conversations even if count fails)

## Success Metrics

A well-functioning conversation_manager should achieve:

- **Reliability:** 99.9% success rate for create/store operations
- **Performance:** < 50ms for message storage, < 200ms for history retrieval (100 messages)
- **User Isolation:** 100% enforcement - zero unauthorized access incidents
- **Data Integrity:** Zero message loss, correct chronological ordering
- **Scalability:** Support 1000+ concurrent conversations without degradation

## Best Practices

### 1. Always Validate User Ownership
```python
# Before ANY operation on a conversation
validate_user_owns_conversation(conversation_id, user_id)
```

### 2. Use Transactions for Multi-Step Operations
```python
# Message storage + timestamp update = one transaction
async with db.transaction():
    insert_message()
    update_conversation_timestamp()
```

### 3. Limit Query Results
```python
# Never query without limits
get_messages(conversation_id, limit=1000)  # ✅
get_messages(conversation_id)  # ❌ Could return millions
```

### 4. Handle Edge Cases
```python
# Empty conversation
if message_count == 0:
    return empty_history_response()

# Very long conversation
if message_count > 1000:
    warn_about_performance()
    apply_pagination()
```

### 5. Log Important Operations
```python
# Log conversation creation, deletions, access violations
logger.info(f"Created conversation {conv_id} for user {user_id}")
logger.warning(f"User {user_id} attempted to access conversation {conv_id} owned by {owner_id}")
```

## Quality Checklist

Before deploying conversation_manager:

- [ ] User isolation enforced in ALL operations
- [ ] Input validation implemented
- [ ] Error handling for all failure modes
- [ ] Transactions used for multi-step operations
- [ ] Database indexes created
- [ ] Query limits applied everywhere
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests written (happy path + errors)
- [ ] Performance tested with 1000+ messages
- [ ] Security review completed
- [ ] Logging implemented
- [ ] Documentation complete

---

**This skill is the foundation of conversation persistence in the stateless architecture!** 💬
