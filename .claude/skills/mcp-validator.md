# MCP Validator Skill

## Purpose
Validate MCP tool calls and responses for the AI todo chatbot. This skill ensures all interactions with MCP tools conform to defined schemas, enforcing input validation, output verification, and security constraints before tool execution and after response receipt.

## Capabilities
- Validate tool names and availability
- Validate tool input parameters against schemas
- Validate tool output responses against expected formats
- Enforce security constraints (user_id presence and format)
- Validate parameter types, lengths, and constraints
- Provide detailed validation error messages
- Verify MCP server connectivity and tool registration
- Sanitize inputs to prevent injection attacks

## Core Responsibilities

### 1. Tool Name Validation
Verify that the requested tool exists and is available.

**Behavior:**
- Check tool name against registered MCP tools
- Ensure tool is one of: add_task, list_tasks, complete_task, update_task, delete_task
- Return clear error if tool not found

**Input:**
```typescript
{
  tool_name: string;
}
```

**Output:**
```typescript
{
  valid: boolean;
  tool_name: string;
  error?: string; // Present if valid=false
}
```

**Validation Rules:**
- Tool name must be non-empty string
- Tool name must exactly match one of the 5 registered tools (case-sensitive)
- Tool name must not contain special characters or spaces

**Error Cases:**
- Empty tool name: `{"valid": false, "error": "Tool name is required"}`
- Unknown tool: `{"valid": false, "error": "Tool 'xyz' not found. Available tools: add_task, list_tasks, complete_task, update_task, delete_task"}`

### 2. Input Parameter Validation
Validate all input parameters before tool execution.

**Behavior:**
- Check required parameters are present
- Validate parameter types match schema
- Enforce length and range constraints
- Validate format constraints
- Check for security issues (injection attempts)

**Input:**
```typescript
{
  tool_name: string;
  parameters: Record<string, any>;
}
```

**Output:**
```typescript
{
  valid: boolean;
  errors: string[]; // List of validation errors
  sanitized_parameters?: Record<string, any>; // Cleaned parameters if valid
}
```

### 3. Tool-Specific Parameter Validation

#### add_task Parameters
**Required:**
- `user_id`: integer, positive, required
- `title`: string, 1-500 characters, required

**Optional:**
- `description`: string, 0-2000 characters

**Validation Rules:**
```typescript
{
  user_id: {
    type: "integer",
    required: true,
    min: 1,
    error_messages: {
      missing: "user_id is required",
      invalid_type: "user_id must be an integer",
      out_of_range: "user_id must be positive"
    }
  },
  title: {
    type: "string",
    required: true,
    minLength: 1,
    maxLength: 500,
    error_messages: {
      missing: "title is required and cannot be empty",
      too_short: "title cannot be empty",
      too_long: "title must be 500 characters or less"
    }
  },
  description: {
    type: "string",
    required: false,
    maxLength: 2000,
    error_messages: {
      too_long: "description must be 2000 characters or less"
    }
  }
}
```

#### list_tasks Parameters
**Required:**
- `user_id`: integer, positive, required

**Optional:**
- `completed`: boolean

**Validation Rules:**
```typescript
{
  user_id: {
    type: "integer",
    required: true,
    min: 1,
    error_messages: {
      missing: "user_id is required",
      invalid_type: "user_id must be an integer",
      out_of_range: "user_id must be positive"
    }
  },
  completed: {
    type: "boolean",
    required: false,
    error_messages: {
      invalid_type: "completed must be a boolean value"
    }
  }
}
```

#### complete_task Parameters
**Required:**
- `user_id`: integer, positive, required
- `task_id`: integer, positive, required

**Validation Rules:**
```typescript
{
  user_id: {
    type: "integer",
    required: true,
    min: 1,
    error_messages: {
      missing: "user_id is required",
      invalid_type: "user_id must be an integer",
      out_of_range: "user_id must be positive"
    }
  },
  task_id: {
    type: "integer",
    required: true,
    min: 1,
    error_messages: {
      missing: "task_id is required",
      invalid_type: "task_id must be an integer",
      out_of_range: "task_id must be positive"
    }
  }
}
```

#### update_task Parameters
**Required:**
- `user_id`: integer, positive, required
- `task_id`: integer, positive, required

**Optional (at least one required):**
- `title`: string, 1-500 characters
- `description`: string, 0-2000 characters

**Validation Rules:**
```typescript
{
  user_id: {
    type: "integer",
    required: true,
    min: 1
  },
  task_id: {
    type: "integer",
    required: true,
    min: 1
  },
  title: {
    type: "string",
    required: false,
    minLength: 1,
    maxLength: 500,
    conditional: "At least one of title or description must be provided"
  },
  description: {
    type: "string",
    required: false,
    maxLength: 2000,
    conditional: "At least one of title or description must be provided"
  }
}
```

**Special Validation:**
- Must provide at least one of: title or description
- Error if neither provided: `{"valid": false, "error": "At least one field (title or description) must be provided"}`

#### delete_task Parameters
**Required:**
- `user_id`: integer, positive, required
- `task_id`: integer, positive, required

**Validation Rules:**
```typescript
{
  user_id: {
    type: "integer",
    required: true,
    min: 1
  },
  task_id: {
    type: "integer",
    required: true,
    min: 1
  }
}
```

### 4. Output Response Validation
Validate tool responses match expected schema.

**Behavior:**
- Verify response contains required fields
- Validate response structure matches schema
- Check data types in response
- Ensure success/error format consistency

**Input:**
```typescript
{
  tool_name: string;
  response: any;
}
```

**Output:**
```typescript
{
  valid: boolean;
  errors: string[];
  validated_response?: any; // Typed response if valid
}
```

### 5. Response Schema Validation

#### add_task Response
**Success Response:**
```typescript
{
  success: true,
  task: {
    id: number;
    user_id: number;
    title: string;
    description: string | null;
    completed: boolean;
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
  }
}
```

**Validation:**
- `success` must be boolean
- If `success=true`, `task` object must be present
- `task.id` must be positive integer
- `task.user_id` must be positive integer
- `task.title` must be non-empty string
- `task.completed` must be boolean
- `task.created_at` must be valid ISO 8601 timestamp
- `task.updated_at` must be valid ISO 8601 timestamp

#### list_tasks Response
**Success Response:**
```typescript
{
  success: true,
  tasks: Task[];
  count: number;
}
```

**Validation:**
- `success` must be boolean
- If `success=true`, `tasks` must be array
- `count` must match `tasks.length`
- Each task must validate as Task object
- Empty array is valid

#### complete_task Response
**Success Response:**
```typescript
{
  success: true,
  task: Task; // with completed=true
}
```

**Validation:**
- Same as add_task response
- `task.completed` must be `true`

#### update_task Response
**Success Response:**
```typescript
{
  success: true,
  task: Task; // with updated fields
}
```

**Validation:**
- Same as add_task response
- `task.updated_at` must be newer than original

#### delete_task Response
**Success Response:**
```typescript
{
  success: true,
  message: string;
  deleted_task_id: number;
}
```

**Validation:**
- `success` must be boolean
- If `success=true`, `deleted_task_id` must be present
- `deleted_task_id` must be positive integer
- `message` must be non-empty string

#### Error Response (All Tools)
**Error Format:**
```typescript
{
  success: false,
  error: string;
}
```

**Validation:**
- `success` must be `false`
- `error` must be non-empty string
- `error` should not expose internal implementation details

### 6. Security Validation
Enforce security constraints on all tool calls.

**Behavior:**
- Ensure user_id is always present
- Validate user_id format
- Check for SQL injection attempts
- Sanitize string inputs
- Validate parameter types to prevent type confusion attacks

**Security Rules:**

**user_id Validation:**
```python
# Conceptual validation
def validate_user_id(user_id):
    # Must be present
    if user_id is None:
        raise ValidationError("user_id is required")

    # Must be integer type
    if not isinstance(user_id, int):
        raise ValidationError("user_id must be an integer")

    # Must be positive
    if user_id < 1:
        raise ValidationError("user_id must be positive")

    return user_id
```

**String Input Sanitization:**
```python
# Conceptual sanitization
def sanitize_string(value, max_length):
    # Remove null bytes
    if '\x00' in value:
        raise ValidationError("String contains invalid null bytes")

    # Check length
    if len(value) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")

    # Validate Unicode
    try:
        value.encode('utf-8')
    except UnicodeEncodeError:
        raise ValidationError("String contains invalid characters")

    return value
```

**Injection Prevention:**
```python
# Conceptual validation
def validate_no_injection(value):
    # Check for common SQL injection patterns (basic check)
    dangerous_patterns = [
        '--', ';--', '/*', '*/', 'xp_', 'sp_',
        'UNION', 'SELECT', 'DROP', 'INSERT', 'DELETE', 'UPDATE'
    ]

    value_upper = str(value).upper()
    for pattern in dangerous_patterns:
        if pattern in value_upper:
            # Log security event
            logger.warning(f"Potential injection attempt detected: {pattern}")
            raise SecurityValidationError("Invalid input detected")

    return value
```

## Usage Examples

### Example 1: Validate add_task Call
```typescript
// Before calling MCP tool
const validation_result = await mcp_validator.validate_input({
  tool_name: "add_task",
  parameters: {
    user_id: 123,
    title: "Buy groceries",
    description: "Milk, bread, eggs"
  }
});

if (!validation_result.valid) {
  // Handle validation errors
  console.error("Validation failed:", validation_result.errors);
  return {
    success: false,
    error: validation_result.errors.join(", ")
  };
}

// Proceed with sanitized parameters
const response = await mcp_tool.add_task(validation_result.sanitized_parameters);

// Validate response
const response_validation = await mcp_validator.validate_output({
  tool_name: "add_task",
  response: response
});

if (!response_validation.valid) {
  // Handle invalid response
  logger.error("Invalid tool response:", response_validation.errors);
  throw new Error("Tool returned invalid response");
}

return response_validation.validated_response;
```

### Example 2: Validate Missing Required Parameter
```typescript
const validation_result = await mcp_validator.validate_input({
  tool_name: "add_task",
  parameters: {
    user_id: 123
    // title is missing!
  }
});

// Returns:
// {
//   valid: false,
//   errors: ["title is required and cannot be empty"]
// }
```

### Example 3: Validate Invalid Parameter Type
```typescript
const validation_result = await mcp_validator.validate_input({
  tool_name: "complete_task",
  parameters: {
    user_id: "not_a_number", // Wrong type!
    task_id: 10
  }
});

// Returns:
// {
//   valid: false,
//   errors: ["user_id must be an integer"]
// }
```

### Example 4: Validate update_task Special Rules
```typescript
const validation_result = await mcp_validator.validate_input({
  tool_name: "update_task",
  parameters: {
    user_id: 123,
    task_id: 10
    // Neither title nor description provided!
  }
});

// Returns:
// {
//   valid: false,
//   errors: ["At least one field (title or description) must be provided"]
// }
```

### Example 5: Validate Tool Response
```typescript
const response = {
  success: true,
  task: {
    id: 123,
    user_id: 456,
    title: "Buy groceries",
    description: null,
    completed: false,
    created_at: "2025-12-19T10:30:00Z",
    updated_at: "2025-12-19T10:30:00Z"
  }
};

const validation_result = await mcp_validator.validate_output({
  tool_name: "add_task",
  response: response
});

// Returns:
// {
//   valid: true,
//   errors: [],
//   validated_response: { success: true, task: {...} }
// }
```

### Example 6: Detect Invalid Response Structure
```typescript
const response = {
  success: true,
  // task object is missing!
};

const validation_result = await mcp_validator.validate_output({
  tool_name: "add_task",
  response: response
});

// Returns:
// {
//   valid: false,
//   errors: ["Response missing required field: task"]
// }
```

## Integration with Other Components

### With OpenAI Agent Orchestrator
The orchestrator uses mcp_validator before and after every MCP tool call.

```typescript
// Orchestrator integration
async function call_mcp_tool(tool_name, parameters) {
  // Step 1: Validate input
  const input_validation = await mcp_validator.validate_input({
    tool_name,
    parameters
  });

  if (!input_validation.valid) {
    // Return validation errors to user
    return {
      success: false,
      error: input_validation.errors.join(", ")
    };
  }

  // Step 2: Call MCP tool with sanitized parameters
  let response;
  try {
    response = await mcp_tool[tool_name](input_validation.sanitized_parameters);
  } catch (error) {
    // Handle tool execution errors
    logger.error(`MCP tool ${tool_name} failed:`, error);
    return {
      success: false,
      error: "Tool execution failed. Please try again."
    };
  }

  // Step 3: Validate output
  const output_validation = await mcp_validator.validate_output({
    tool_name,
    response
  });

  if (!output_validation.valid) {
    // Log invalid response but don't expose to user
    logger.error(`MCP tool ${tool_name} returned invalid response:`,
                 output_validation.errors);
    return {
      success: false,
      error: "Invalid response from tool. Please contact support."
    };
  }

  // Step 4: Return validated response
  return output_validation.validated_response;
}
```

### With MCP Server
The MCP server can use validator on tool registration.

```typescript
// MCP server startup validation
async function register_tools() {
  const tools = ['add_task', 'list_tasks', 'complete_task', 'update_task', 'delete_task'];

  for (const tool_name of tools) {
    // Validate tool is available
    const validation = await mcp_validator.validate_tool_name({ tool_name });

    if (!validation.valid) {
      throw new Error(`Failed to register tool ${tool_name}: ${validation.error}`);
    }

    logger.info(`Tool ${tool_name} registered successfully`);
  }
}
```

## Validation Error Types

```typescript
{
  MissingParameterError: {
    code: "MISSING_PARAMETER",
    message: "{parameter} is required"
  },
  InvalidTypeError: {
    code: "INVALID_TYPE",
    message: "{parameter} must be {expected_type}"
  },
  LengthConstraintError: {
    code: "LENGTH_CONSTRAINT",
    message: "{parameter} must be between {min} and {max} characters"
  },
  RangeConstraintError: {
    code: "RANGE_CONSTRAINT",
    message: "{parameter} must be between {min} and {max}"
  },
  UnknownToolError: {
    code: "UNKNOWN_TOOL",
    message: "Tool '{tool_name}' not found. Available tools: {available_tools}"
  },
  ConditionalParameterError: {
    code: "CONDITIONAL_PARAMETER",
    message: "At least one of {parameters} must be provided"
  },
  SecurityValidationError: {
    code: "SECURITY_VALIDATION",
    message: "Invalid input detected"
  },
  InvalidResponseError: {
    code: "INVALID_RESPONSE",
    message: "Response missing required field: {field}"
  },
  ResponseTypeError: {
    code: "RESPONSE_TYPE",
    message: "Response field {field} has invalid type (expected {expected})"
  }
}
```

## Validation Checklist

Before allowing tool execution:

- [ ] Tool name is valid and registered
- [ ] All required parameters are present
- [ ] All parameters have correct types
- [ ] String parameters within length limits
- [ ] Integer parameters within range constraints
- [ ] user_id is present and positive integer
- [ ] No SQL injection patterns detected
- [ ] No null bytes in strings
- [ ] Valid UTF-8 encoding in strings
- [ ] Conditional parameters satisfied (update_task)

After receiving tool response:

- [ ] Response has success field (boolean)
- [ ] If success=true, required response fields present
- [ ] All response fields have correct types
- [ ] Timestamps are valid ISO 8601 format
- [ ] Integer IDs are positive
- [ ] Arrays are proper type (for list_tasks)
- [ ] Error messages don't expose internals
- [ ] Response structure matches schema

## Performance Considerations

### Fast Validation
- **Validation Speed:** All validations complete in < 10ms
- **No Network Calls:** All validation is local/in-memory
- **Minimal Overhead:** Validation adds < 5% to total request time

### Caching Tool Schemas
```python
# Conceptual caching
class MCPValidator:
    def __init__(self):
        # Cache tool schemas on initialization
        self.tool_schemas = {
            'add_task': AddTaskSchema,
            'list_tasks': ListTasksSchema,
            'complete_task': CompleteTaskSchema,
            'update_task': UpdateTaskSchema,
            'delete_task': DeleteTaskSchema
        }

    def validate_input(self, tool_name, parameters):
        # O(1) schema lookup
        schema = self.tool_schemas.get(tool_name)
        if not schema:
            return invalid_tool_error(tool_name)

        return schema.validate(parameters)
```

## Testing Strategy

### Unit Tests
```python
# Conceptual test cases
def test_validate_add_task_with_valid_params():
    result = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={
            "user_id": 123,
            "title": "Test task",
            "description": "Test description"
        }
    )
    assert result.valid == True
    assert len(result.errors) == 0

def test_validate_add_task_missing_title():
    result = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={
            "user_id": 123
        }
    )
    assert result.valid == False
    assert "title is required" in result.errors

def test_validate_add_task_title_too_long():
    result = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={
            "user_id": 123,
            "title": "x" * 501  # Exceeds 500 char limit
        }
    )
    assert result.valid == False
    assert "title must be 500 characters or less" in result.errors

def test_validate_update_task_no_fields():
    result = mcp_validator.validate_input(
        tool_name="update_task",
        parameters={
            "user_id": 123,
            "task_id": 10
            # Neither title nor description provided
        }
    )
    assert result.valid == False
    assert "At least one field (title or description) must be provided" in result.errors

def test_validate_response_add_task_success():
    response = {
        "success": True,
        "task": {
            "id": 123,
            "user_id": 456,
            "title": "Test",
            "description": None,
            "completed": False,
            "created_at": "2025-12-19T10:30:00Z",
            "updated_at": "2025-12-19T10:30:00Z"
        }
    }
    result = mcp_validator.validate_output(
        tool_name="add_task",
        response=response
    )
    assert result.valid == True
    assert len(result.errors) == 0

def test_validate_response_missing_task_field():
    response = {
        "success": True
        # task field missing!
    }
    result = mcp_validator.validate_output(
        tool_name="add_task",
        response=response
    )
    assert result.valid == False
    assert "Response missing required field: task" in result.errors

def test_security_validation_sql_injection():
    result = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={
            "user_id": 123,
            "title": "Test'; DROP TABLE tasks; --"
        }
    )
    assert result.valid == False
    assert "Invalid input detected" in result.errors

def test_security_validation_null_bytes():
    result = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={
            "user_id": 123,
            "title": "Test\x00malicious"
        }
    )
    assert result.valid == False
    assert "invalid null bytes" in str(result.errors).lower()
```

### Integration Tests
```python
# Conceptual integration tests
def test_full_validation_flow():
    # Validate input
    input_validation = mcp_validator.validate_input(
        tool_name="add_task",
        parameters={"user_id": 123, "title": "Test"}
    )
    assert input_validation.valid == True

    # Simulate tool call
    response = {
        "success": True,
        "task": {
            "id": 456,
            "user_id": 123,
            "title": "Test",
            "description": None,
            "completed": False,
            "created_at": "2025-12-19T10:30:00Z",
            "updated_at": "2025-12-19T10:30:00Z"
        }
    }

    # Validate output
    output_validation = mcp_validator.validate_output(
        tool_name="add_task",
        response=response
    )
    assert output_validation.valid == True
```

## Error Recovery

### Graceful Degradation
- If validation fails, provide clear error message to user
- Log validation failures for monitoring
- Never expose internal validation logic to end users
- Fail securely (reject on validation error, not allow)

### Logging Strategy
```python
# Conceptual logging
def validate_input(tool_name, parameters):
    try:
        # Perform validation
        result = validate_parameters(tool_name, parameters)

        if not result.valid:
            # Log validation failure
            logger.warning(
                f"Input validation failed for {tool_name}",
                extra={
                    "tool": tool_name,
                    "errors": result.errors,
                    "parameters_keys": list(parameters.keys())
                    # Don't log actual parameter values (may contain sensitive data)
                }
            )

        return result
    except Exception as e:
        # Log unexpected validation errors
        logger.error(
            f"Validation exception for {tool_name}: {str(e)}",
            exc_info=True
        )
        # Fail securely
        return {
            "valid": False,
            "errors": ["Validation failed. Please try again."]
        }
```

## Success Metrics

A well-functioning mcp_validator should achieve:

- **Validation Accuracy:** 100% - No false positives or false negatives
- **Performance:** < 10ms validation time per call
- **Security:** 100% - All injection attempts detected and blocked
- **Coverage:** 100% - All 5 tools and all parameters validated
- **Error Clarity:** 100% - All validation errors have clear, actionable messages
- **Reliability:** 99.9%+ - Validator never crashes or causes tool failures

## Best Practices

### 1. Always Validate Before Tool Execution
```python
# ✅ Correct
validation = validate_input(tool_name, parameters)
if validation.valid:
    result = call_tool(validation.sanitized_parameters)
else:
    return validation_error(validation.errors)

# ❌ Wrong
result = call_tool(parameters)  # No validation!
```

### 2. Use Sanitized Parameters
```python
# ✅ Correct
params = validation.sanitized_parameters
result = call_tool(params)

# ❌ Wrong
result = call_tool(original_parameters)  # Use sanitized!
```

### 3. Validate Responses
```python
# ✅ Correct
response = call_tool(params)
output_validation = validate_output(tool_name, response)
if output_validation.valid:
    return output_validation.validated_response

# ❌ Wrong
return response  # No output validation!
```

### 4. Log Validation Failures
```python
# ✅ Correct
if not validation.valid:
    logger.warning(f"Validation failed: {validation.errors}")
    return error_response(validation.errors)

# ❌ Wrong
if not validation.valid:
    return error_response(validation.errors)  # No logging!
```

### 5. Never Expose Internal Details
```python
# ✅ Correct
return {
    "success": False,
    "error": "title must be 500 characters or less"
}

# ❌ Wrong
return {
    "success": False,
    "error": "SQLAlchemy column title max_length constraint violated at line 42"
}
```

## Quality Checklist

Before deploying mcp_validator:

- [ ] All 5 tools have complete parameter schemas
- [ ] All required parameters are validated
- [ ] All optional parameters are validated when present
- [ ] Type validation implemented for all parameters
- [ ] Length constraints enforced for strings
- [ ] Range constraints enforced for integers
- [ ] Security validation (injection, null bytes) implemented
- [ ] Output validation for all tool response types
- [ ] Error messages are clear and actionable
- [ ] Error messages don't expose internal details
- [ ] Unit tests cover all validation rules (100+ test cases)
- [ ] Integration tests cover validation flow
- [ ] Performance tested (< 10ms validation time)
- [ ] Security tested (injection attempts blocked)
- [ ] Logging implemented for failures
- [ ] Documentation complete

---

**This skill ensures all MCP tool interactions are secure, valid, and compliant with schemas!** 🛡️
