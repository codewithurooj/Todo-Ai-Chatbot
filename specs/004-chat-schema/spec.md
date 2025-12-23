# Feature Specification: Chat Conversation Database Schema

**Feature Branch**: `004-chat-schema`
**Created**: 2025-12-19
**Status**: Draft
**Input**: User description: "Database schema for Phase III chatbot conversations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persist New Conversations (Priority: P1)

When a user starts their first interaction with the chatbot, the system creates a new conversation record to group all subsequent messages in that chat session.

**Why this priority**: Without conversation persistence, the system cannot maintain stateless architecture or provide conversation history. This is foundational for all chat functionality.

**Independent Test**: User sends their first message to the chatbot. System creates a conversation record with unique ID, user association, and timestamps, then stores the message. Value delivered: Conversation context is preserved across server restarts.

**Acceptance Scenarios**:

1. **Given** a user with id=123 sends their first message to the chatbot, **When** the system processes the request, **Then** it creates a conversation record with user_id=123, unique conversation ID, and creation timestamp
2. **Given** a user starts a new conversation, **When** the conversation is created, **Then** both created_at and updated_at timestamps are set to the current time
3. **Given** a conversation is created, **When** queried by conversation_id, **Then** the system returns the conversation with all field values intact
4. **Given** a user creates multiple conversations, **When** querying conversations by user_id, **Then** the system returns only that user's conversations (user isolation)

---

### User Story 2 - Store Messages in Conversations (Priority: P1)

Every message sent by either the user or the AI assistant is stored in the database, associated with its parent conversation, preserving the complete exchange history.

**Why this priority**: Message storage is essential for conversation context, allowing the AI to reference previous messages and maintain continuity across interactions.

**Independent Test**: User sends message "add buy groceries" in conversation 456. System stores message with content, role=user, conversation link, and timestamp. AI response is also stored with role=assistant. Value delivered: Complete conversation history available for retrieval.

**Acceptance Scenarios**:

1. **Given** a conversation with id=456 exists, **When** user sends message "add buy groceries", **Then** system creates message record with conversation_id=456, role=user, content="add buy groceries", user_id, and creation timestamp
2. **Given** a user message is stored, **When** AI generates response "I've added 'Buy groceries' to your list", **Then** system creates message record with same conversation_id, role=assistant, response content, and timestamp
3. **Given** a conversation has 10 messages, **When** retrieving messages for that conversation_id, **Then** system returns all 10 messages ordered by creation time (oldest first)
4. **Given** user 123 has messages in conversation A, **When** user 456 tries to access conversation A, **Then** system prevents access (enforces user isolation at conversation level)

---

### User Story 3 - Retrieve Conversation History (Priority: P1)

When processing a new user message, the system retrieves the complete conversation history (all previous messages) to provide context to the AI agent for generating relevant responses.

**Why this priority**: Conversation context enables multi-turn interactions and allows the AI to understand references to previous tasks or statements.

**Independent Test**: User sends 5th message in ongoing conversation. System retrieves all 4 previous messages (2 user, 2 assistant) in chronological order before processing new message. Value delivered: AI has full context for intelligent responses.

**Acceptance Scenarios**:

1. **Given** a conversation has 8 stored messages, **When** system retrieves history for that conversation, **Then** it returns all 8 messages ordered chronologically (oldest to newest)
2. **Given** a conversation has messages from different roles, **When** retrieving history, **Then** system preserves correct role attribution (user vs assistant) for each message
3. **Given** a user references "the task I mentioned earlier" in message 5, **When** system provides previous 4 messages to AI, **Then** AI can locate referenced task from message 2
4. **Given** a conversation hasn't been accessed in 30 days, **When** retrieving its history, **Then** all messages are still available (no automatic expiration)

---

### User Story 4 - Support Multiple Concurrent Conversations (Priority: P2)

Users can start new conversations while keeping previous conversations accessible, allowing them to organize different chat contexts or topics separately.

**Why this priority**: While users can accomplish everything in a single conversation, multiple conversations improve organization and allow users to separate different contexts or time periods.

**Independent Test**: User has active conversation 100 with 10 messages. User starts new conversation 101. Both conversations remain accessible independently with their respective message histories. Value delivered: Flexible conversation management.

**Acceptance Scenarios**:

1. **Given** user 123 has conversation A with 5 messages, **When** they start a new conversation B, **Then** conversation A remains unchanged with its 5 messages intact
2. **Given** user has conversations A (10 messages) and B (3 messages), **When** retrieving messages for conversation A, **Then** system returns only the 10 messages from A (no cross-contamination)
3. **Given** user has 5 conversations, **When** listing all conversations for that user, **Then** system returns all 5 with their metadata (id, created_at, updated_at)
4. **Given** user creates conversation B after conversation A, **When** listing conversations, **Then** they are ordered by creation time (newest or oldest first per query parameter)

---

### User Story 5 - Track Conversation Activity (Priority: P3)

Each conversation record tracks when it was last updated, allowing the system to identify active vs stale conversations and present them accordingly to users.

**Why this priority**: While not critical for core functionality, activity tracking helps users find recent conversations and supports potential future features like archiving or cleanup.

**Independent Test**: User sends new message in conversation 789. System updates conversation's updated_at timestamp to current time. Value delivered: Conversations sorted by recency show most active chats first.

**Acceptance Scenarios**:

1. **Given** conversation 789 with updated_at="2025-12-19 10:00", **When** user adds new message at "2025-12-19 15:30", **Then** conversation's updated_at changes to "2025-12-19 15:30"
2. **Given** user has conversations with various updated_at times, **When** querying conversations ordered by updated_at descending, **Then** most recently active conversation appears first
3. **Given** a conversation's updated_at differs from created_at, **When** retrieved, **Then** both timestamps are preserved showing creation time and last activity time
4. **Given** user views conversation list, **When** sorted by recency, **Then** conversations with activity today appear before conversations from last week

---

### Edge Cases

- What happens when a conversation has thousands of messages (e.g., very long chat session)?
- How does the system handle concurrent message inserts to the same conversation from multiple requests?
- What happens if a message exceeds expected length limits (e.g., 100,000 characters)?
- How does the system prevent orphaned messages (messages with non-existent conversation_id)?
- What happens when retrieving messages for a conversation that was just deleted?
- How are timestamps handled for users in different timezones?
- What happens if the same user tries to create duplicate conversations simultaneously?
- How does the system handle special characters, emojis, or code blocks in message content?

## Requirements *(mandatory)*

### Functional Requirements

#### Conversations Table

- **FR-001**: Conversations table MUST have a unique identifier field (integer, auto-incrementing primary key)
- **FR-002**: Conversations table MUST have a user_id field (integer, required) linking to the owning user
- **FR-003**: Conversations table MUST have a created_at field (timestamp, required) recording conversation creation time
- **FR-004**: Conversations table MUST have an updated_at field (timestamp, required) recording last activity time
- **FR-005**: Conversations table MUST enforce user_id as a required field (cannot be null)
- **FR-006**: Conversations table MUST support querying all conversations for a specific user_id
- **FR-007**: Conversations table MUST support ordering by created_at or updated_at for recency sorting
- **FR-008**: Conversations table MUST maintain referential integrity with the users table (foreign key)

#### Messages Table

- **FR-009**: Messages table MUST have a unique identifier field (integer, auto-incrementing primary key)
- **FR-010**: Messages table MUST have a conversation_id field (integer, required) linking to parent conversation
- **FR-011**: Messages table MUST have a user_id field (integer, required) for user isolation and auditing
- **FR-012**: Messages table MUST have a role field (string/enum, required) indicating "user" or "assistant"
- **FR-013**: Messages table MUST have a content field (text, required) storing the message text
- **FR-014**: Messages table MUST have a created_at field (timestamp, required) recording message creation time
- **FR-015**: Messages table MUST enforce all required fields as non-null
- **FR-016**: Messages table MUST maintain referential integrity with conversations table (foreign key on conversation_id)
- **FR-017**: Messages table MUST maintain referential integrity with users table (foreign key on user_id)
- **FR-018**: Messages table MUST support querying all messages for a specific conversation_id
- **FR-019**: Messages table MUST support ordering by created_at for chronological message retrieval
- **FR-020**: Messages table MUST store content field with sufficient capacity for long messages (at least 10,000 characters)

#### Relationships and Constraints

- **FR-021**: One conversation MUST belong to exactly one user (one-to-many: user to conversations)
- **FR-022**: One conversation CAN contain zero or more messages (one-to-many: conversation to messages)
- **FR-023**: One message MUST belong to exactly one conversation
- **FR-024**: One message MUST be associated with exactly one user (matches conversation owner)
- **FR-025**: Deleting a conversation MUST handle associated messages appropriately (cascade delete or prevent deletion)
- **FR-026**: System MUST prevent creating messages with conversation_id that doesn't exist
- **FR-027**: System MUST prevent creating messages with user_id that doesn't match conversation owner
- **FR-028**: System MUST ensure created_at timestamps are immutable after record creation

#### Data Integrity and Isolation

- **FR-029**: System MUST enforce user data isolation - users can only access their own conversations
- **FR-030**: System MUST enforce user data isolation - users can only access messages from their conversations
- **FR-031**: System MUST ensure conversation.user_id matches message.user_id for all messages in that conversation
- **FR-032**: System MUST maintain timestamp consistency (created_at cannot be in the future)
- **FR-033**: System MUST update conversation.updated_at when new messages are added
- **FR-034**: System MUST preserve all timestamps in UTC format for consistency across timezones

### Key Entities

- **Conversation**: Represents a chat session between a user and the AI assistant. Key attributes:
  - `id` (integer, unique identifier, auto-generated)
  - `user_id` (integer, owner of the conversation, required)
  - `created_at` (timestamp, when conversation started, required)
  - `updated_at` (timestamp, last activity time, required, auto-updated)
  - Relationships: belongs to one User, has many Messages

- **Message**: Represents a single exchange in a conversation (either user input or assistant response). Key attributes:
  - `id` (integer, unique identifier, auto-generated)
  - `conversation_id` (integer, parent conversation, required)
  - `user_id` (integer, for data isolation, required)
  - `role` (string/enum: "user" or "assistant", required)
  - `content` (text, message content, required, supports 10,000+ characters)
  - `created_at` (timestamp, when message was sent, required)
  - Relationships: belongs to one Conversation, belongs to one User

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System can store and retrieve conversations with all fields intact - 100% data fidelity
- **SC-002**: System can store individual messages up to 10,000 characters without data loss or truncation
- **SC-003**: Conversation history retrieval completes in under 500ms for conversations with up to 100 messages
- **SC-004**: System enforces user isolation - zero instances of users accessing other users' conversations or messages
- **SC-005**: System maintains referential integrity - zero orphaned messages (messages without valid conversation_id)
- **SC-006**: Timestamps are consistently stored in UTC across all records
- **SC-007**: System supports at least 10,000 concurrent conversations without performance degradation
- **SC-008**: Message retrieval maintains chronological order for 100% of conversations
- **SC-009**: Conversation updated_at timestamp updates within 1 second of new message insertion
- **SC-010**: System prevents cross-conversation message contamination - messages always linked to correct conversation

### User Experience Outcomes

- **SC-011**: Users can access complete conversation history from any session - no data loss on server restart
- **SC-012**: Conversation context enables AI to reference previous messages accurately in responses
- **SC-013**: Users can maintain separate conversations for different topics or time periods
- **SC-014**: Most recent conversations appear first when users view conversation list

## Assumptions *(mandatory)*

- User authentication is handled outside the database schema (JWT validation at application layer)
- User table exists with appropriate structure (id, authentication fields)
- Database supports auto-incrementing integer primary keys
- Database supports timestamp data types with timezone awareness
- Database enforces foreign key constraints
- Messages are primarily text-based (no binary attachments in Phase III)
- Average conversation has between 10-50 messages
- Maximum message length requirement is 10,000 characters (sufficient for code blocks, long responses)
- Conversations do not have automatic expiration (persist indefinitely)
- Message edit/delete functionality is out of scope (messages are immutable once created)
- Database connection pooling and transaction management handled at application layer
- Concurrent access controlled by database transaction isolation levels

## Table Structures *(mandatory for this spec)*

### Conversations Table

**Purpose**: Stores chat sessions between users and the AI assistant

**Fields**:

| Field Name   | Data Type | Constraints           | Description                              |
|--------------|-----------|----------------------|------------------------------------------|
| id           | Integer   | Primary Key, Auto-increment | Unique conversation identifier     |
| user_id      | Integer   | Required, Foreign Key | Owner of the conversation               |
| created_at   | Timestamp | Required, Auto-set   | When conversation was created (UTC)     |
| updated_at   | Timestamp | Required, Auto-update| Last activity time (UTC)                |

**Relationships**:
- `user_id` references users table (many-to-one)
- Referenced by messages table via `conversation_id` (one-to-many)

**Indexes** (for performance):
- Primary index on `id`
- Index on `user_id` for user conversation queries
- Index on `updated_at` for recency sorting

---

### Messages Table

**Purpose**: Stores individual messages within conversations (both user and assistant messages)

**Fields**:

| Field Name      | Data Type    | Constraints           | Description                              |
|-----------------|--------------|----------------------|------------------------------------------|
| id              | Integer      | Primary Key, Auto-increment | Unique message identifier          |
| conversation_id | Integer      | Required, Foreign Key | Parent conversation                     |
| user_id         | Integer      | Required, Foreign Key | User for data isolation                 |
| role            | String/Enum  | Required, Values: "user" or "assistant" | Message sender    |
| content         | Text         | Required, Min: 1 char, Max: 10,000+ chars | Message content |
| created_at      | Timestamp    | Required, Auto-set   | When message was sent (UTC)             |

**Relationships**:
- `conversation_id` references conversations table (many-to-one)
- `user_id` references users table (many-to-one)

**Indexes** (for performance):
- Primary index on `id`
- Index on `conversation_id` for message retrieval
- Index on `created_at` for chronological ordering within conversation

**Constraints**:
- `user_id` must match the `user_id` of the parent conversation (application-level check)
- `role` must be either "user" or "assistant"
- `conversation_id` must exist in conversations table (foreign key constraint)

---

## Entity Relationship Diagram (Textual)

```
User (1) ----< Conversations (many)
  |
  |
  └---------< Messages (many)

Conversation (1) ----< Messages (many)

Constraints:
- Each Conversation belongs to exactly one User
- Each Message belongs to exactly one Conversation
- Each Message's user_id MUST match its Conversation's user_id
- Messages ordered by created_at within each Conversation
- Conversation.updated_at updates when Messages are added
```

## Out of Scope

- Message edit or update functionality (messages are immutable)
- Message deletion by users (conversations can be deleted as a whole)
- Message threading or replies (flat conversation structure)
- Message reactions, likes, or annotations
- Rich media storage (images, files, voice) within messages
- Message search or full-text indexing
- Conversation archiving or soft delete
- Conversation sharing between users
- Message read/unread status tracking
- Typing indicators or presence status
- Conversation tagging or categorization
- Message delivery or read receipts
- Pagination strategy for very large conversations (handled at application layer)
- Database replication or backup strategy (infrastructure concern)

## Dependencies

- Users table must exist with id field as primary key
- Database must support foreign key constraints
- Database must support timestamp data types
- Database must support auto-incrementing integer primary keys
- Database must support text fields with 10,000+ character capacity
- Database connection from application layer (DATABASE_URL environment variable)

## Risks & Mitigations

1. **Risk**: Very long conversations (1000+ messages) may have slow retrieval times
   - **Mitigation**: Create index on conversation_id and created_at for efficient message queries. Consider pagination at application layer for conversations exceeding 100 messages.

2. **Risk**: Concurrent message inserts to same conversation could cause race conditions on updated_at
   - **Mitigation**: Use database transaction isolation and optimistic locking. Handle update conflicts gracefully at application layer.

3. **Risk**: Message content exceeds 10,000 character limit
   - **Mitigation**: Validate message length at application layer before database insert. Return clear error message to AI agent if limit exceeded.

4. **Risk**: User_id mismatch between message and conversation causes data isolation breach
   - **Mitigation**: Enforce check at application layer before insert. Add database trigger or check constraint if supported.

5. **Risk**: Orphaned messages if conversation is deleted
   - **Mitigation**: Use cascade delete on foreign key constraint or prevent conversation deletion if messages exist.

6. **Risk**: Timestamp timezone inconsistencies across deployments
   - **Mitigation**: Always store timestamps in UTC. Convert to user timezone only at presentation layer.
