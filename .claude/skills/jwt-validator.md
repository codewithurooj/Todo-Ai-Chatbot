# JWT Validator Skill

## Purpose
Validate and decode JWT (JSON Web Token) authentication tokens for the AI todo chatbot API. This skill ensures all API requests are properly authenticated, tokens are valid and unexpired, and user claims match authorization requirements.

## Capabilities
- Extract JWT tokens from Authorization headers
- Decode and parse JWT structure
- Validate JWT signatures using shared secret
- Verify token expiration (exp claim)
- Extract and validate user claims (user_id, email, etc.)
- Enforce user_id authorization matching
- Provide detailed authentication error messages
- Handle token edge cases (malformed, expired, tampered)

## Core Responsibilities

### 1. Token Extraction
Extract JWT bearer token from HTTP Authorization header.

**Behavior:**
- Parse `Authorization` header
- Validate header format: `Bearer <token>`
- Extract token string
- Return clear error if header missing or malformed

**Input:**
```typescript
{
  authorization_header: string;
}
```

**Output:**
```typescript
{
  valid: boolean;
  token?: string; // Present if valid
  error?: string; // Present if invalid
}
```

**Validation Rules:**
- Header must start with "Bearer " (case-sensitive)
- Token must be non-empty after "Bearer "
- Token must contain exactly 3 parts separated by dots (header.payload.signature)

**Error Cases:**
- Missing header: `{"valid": false, "error": "Authorization header is required"}`
- Wrong format: `{"valid": false, "error": "Authorization header must use Bearer scheme"}`
- Empty token: `{"valid": false, "error": "JWT token is required"}`
- Malformed token: `{"valid": false, "error": "Invalid JWT format (expected 3 parts)"}`

### 2. Token Decoding
Decode JWT structure and parse claims.

**Behavior:**
- Decode Base64Url-encoded header
- Decode Base64Url-encoded payload
- Parse JSON claims from payload
- Return claims object

**Input:**
```typescript
{
  token: string;
}
```

**Output:**
```typescript
{
  valid: boolean;
  claims?: {
    user_id: string | number;
    email?: string;
    exp: number; // Unix timestamp
    iat: number; // Unix timestamp
    [key: string]: any; // Additional claims
  };
  error?: string;
}
```

**Validation Rules:**
- Header and payload must be valid Base64Url
- Payload must be valid JSON
- Claims must include required fields (exp, user_id)

**Error Cases:**
- Invalid Base64: `{"valid": false, "error": "Invalid JWT encoding"}`
- Invalid JSON: `{"valid": false, "error": "Invalid JWT payload format"}`
- Missing exp: `{"valid": false, "error": "JWT missing expiration claim"}`
- Missing user_id: `{"valid": false, "error": "JWT missing user_id claim"}`

### 3. Signature Verification
Verify JWT signature using shared secret.

**Behavior:**
- Extract signature from token
- Compute expected signature using header + payload + secret
- Compare signatures using constant-time comparison
- Return validation result

**Input:**
```typescript
{
  token: string;
  secret: string; // BETTER_AUTH_SECRET from environment
}
```

**Output:**
```typescript
{
  valid: boolean;
  error?: string;
}
```

**Validation Rules:**
- Algorithm must be HS256 (HMAC-SHA256)
- Signature must match computed HMAC
- Use constant-time comparison to prevent timing attacks

**Error Cases:**
- Invalid signature: `{"valid": false, "error": "Invalid token signature"}`
- Unsupported algorithm: `{"valid": false, "error": "Unsupported JWT algorithm (expected HS256)"}`

**Security Pattern:**
```python
# Conceptual signature verification
import hmac
import hashlib

def verify_signature(token, secret):
    parts = token.split('.')
    if len(parts) != 3:
        return False

    header_payload = f"{parts[0]}.{parts[1]}"
    signature = parts[2]

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        header_payload.encode('utf-8'),
        hashlib.sha256
    ).digest()

    # Base64Url encode expected signature
    expected_b64 = base64url_encode(expected_signature)

    # Constant-time comparison
    return hmac.compare_digest(signature, expected_b64)
```

### 4. Expiration Validation
Verify token has not expired.

**Behavior:**
- Extract `exp` claim from token
- Get current Unix timestamp
- Compare current time to expiration
- Return validation result

**Input:**
```typescript
{
  exp: number; // Unix timestamp from token claims
}
```

**Output:**
```typescript
{
  valid: boolean;
  expired: boolean;
  seconds_until_expiry?: number; // Positive if valid, negative if expired
  error?: string;
}
```

**Validation Rules:**
- Current time must be less than exp time
- Allow 30-second clock skew tolerance

**Error Cases:**
- Token expired: `{"valid": false, "expired": true, "error": "Token has expired"}`

**Implementation Pattern:**
```python
# Conceptual expiration check
import time

def validate_expiration(exp_claim):
    current_time = int(time.time())
    # Allow 30-second clock skew
    skew_tolerance = 30

    if current_time > (exp_claim + skew_tolerance):
        return {
            "valid": False,
            "expired": True,
            "error": "Token has expired"
        }

    seconds_until_expiry = exp_claim - current_time
    return {
        "valid": True,
        "expired": False,
        "seconds_until_expiry": seconds_until_expiry
    }
```

### 5. User Authorization Validation
Verify token user_id matches path user_id.

**Behavior:**
- Extract user_id from JWT claims
- Compare to user_id from API path parameter
- Return validation result

**Input:**
```typescript
{
  token_user_id: string | number;
  path_user_id: string | number;
}
```

**Output:**
```typescript
{
  valid: boolean;
  authorized: boolean;
  error?: string;
}
```

**Validation Rules:**
- user_id values must match exactly (after type normalization)
- Both string and numeric user_ids supported
- Comparison is case-sensitive for strings

**Error Cases:**
- Mismatch: `{"valid": false, "authorized": false, "error": "You can only access your own conversations"}`

**Implementation Pattern:**
```python
# Conceptual authorization check
def validate_user_authorization(token_user_id, path_user_id):
    # Normalize to string for comparison
    token_id = str(token_user_id)
    path_id = str(path_user_id)

    if token_id != path_id:
        return {
            "valid": False,
            "authorized": False,
            "error": "You can only access your own conversations"
        }

    return {
        "valid": True,
        "authorized": True
    }
```

### 6. Complete JWT Validation
Full validation pipeline combining all checks.

**Behavior:**
- Extract token from header
- Decode and parse claims
- Verify signature
- Check expiration
- Validate user authorization
- Return comprehensive result

**Input:**
```typescript
{
  authorization_header: string;
  secret: string; // BETTER_AUTH_SECRET
  path_user_id: string | number;
}
```

**Output:**
```typescript
{
  valid: boolean;
  authenticated: boolean;
  authorized: boolean;
  user_id?: string | number; // Present if valid
  claims?: object; // Full JWT claims if valid
  error?: string;
  error_code?: number; // HTTP status code (401, 403)
}
```

**Validation Pipeline:**
1. Extract token from header → 401 if fails
2. Decode token claims → 401 if fails
3. Verify signature → 401 if fails
4. Check expiration → 401 if fails
5. Validate user_id match → 403 if fails

**Success Response:**
```typescript
{
  valid: true,
  authenticated: true,
  authorized: true,
  user_id: "user_123",
  claims: {
    user_id: "user_123",
    email: "user@example.com",
    exp: 1703012345,
    iat: 1703008745
  }
}
```

**Error Response Examples:**
```typescript
// Missing token
{
  valid: false,
  authenticated: false,
  authorized: false,
  error: "Authorization header is required",
  error_code: 401
}

// Invalid signature
{
  valid: false,
  authenticated: false,
  authorized: false,
  error: "Invalid token signature",
  error_code: 401
}

// Expired token
{
  valid: false,
  authenticated: false,
  authorized: false,
  error: "Token has expired",
  error_code: 401
}

// Wrong user
{
  valid: false,
  authenticated: true,
  authorized: false,
  error: "You can only access your own conversations",
  error_code: 403
}
```

## Usage Examples

### Example 1: Complete Validation in API Handler
```typescript
// API endpoint handler
async function handle_chat_request(request) {
  // Extract necessary data
  const auth_header = request.headers.get("Authorization");
  const path_user_id = request.params.user_id;
  const secret = process.env.BETTER_AUTH_SECRET;

  // Validate JWT
  const validation = await jwt_validator.validate_complete({
    authorization_header: auth_header,
    secret: secret,
    path_user_id: path_user_id
  });

  // Handle authentication failure (401)
  if (!validation.authenticated) {
    return {
      status: 401,
      body: {
        error: "Unauthorized",
        message: validation.error
      }
    };
  }

  // Handle authorization failure (403)
  if (!validation.authorized) {
    return {
      status: 403,
      body: {
        error: "Forbidden",
        message: validation.error
      }
    };
  }

  // Proceed with authenticated user_id
  const authenticated_user_id = validation.user_id;

  // Process the request...
  return process_chat_message(authenticated_user_id, request.body);
}
```

### Example 2: Extract Token Only
```typescript
const auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

const extraction = await jwt_validator.extract_token({
  authorization_header: auth_header
});

if (extraction.valid) {
  console.log("Token extracted:", extraction.token);
  // Proceed with token validation
} else {
  console.error("Token extraction failed:", extraction.error);
  // Return 401
}
```

### Example 3: Decode Token Claims
```typescript
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjMiLCJleHAiOjE3MDMwMTIzNDV9...";

const decoded = await jwt_validator.decode_token({
  token: token
});

if (decoded.valid) {
  console.log("User ID:", decoded.claims.user_id);
  console.log("Expires at:", new Date(decoded.claims.exp * 1000));
} else {
  console.error("Token decoding failed:", decoded.error);
}
```

### Example 4: Verify Signature
```typescript
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const secret = process.env.BETTER_AUTH_SECRET;

const signature_check = await jwt_validator.verify_signature({
  token: token,
  secret: secret
});

if (signature_check.valid) {
  console.log("Signature valid - token is authentic");
} else {
  console.error("Invalid signature - token may be tampered");
  // Return 401 - token is not trustworthy
}
```

### Example 5: Check Expiration
```typescript
const exp_claim = 1703012345; // Unix timestamp from token

const expiration_check = await jwt_validator.validate_expiration({
  exp: exp_claim
});

if (expiration_check.valid) {
  console.log(`Token valid for ${expiration_check.seconds_until_expiry} more seconds`);
} else {
  console.error("Token expired:", expiration_check.error);
  // Return 401 - user must re-authenticate
}
```

### Example 6: Validate User Authorization
```typescript
const token_user_id = "user_123"; // From JWT claims
const path_user_id = "user_123"; // From API path /api/user_123/chat

const auth_check = await jwt_validator.validate_user_authorization({
  token_user_id: token_user_id,
  path_user_id: path_user_id
});

if (auth_check.authorized) {
  console.log("User authorized to access this resource");
} else {
  console.error("Authorization failed:", auth_check.error);
  // Return 403 - user trying to access another user's data
}
```

### Example 7: Handle Missing Authorization Header
```typescript
const request_without_auth = {
  headers: {} // No Authorization header
};

const validation = await jwt_validator.validate_complete({
  authorization_header: undefined,
  secret: process.env.BETTER_AUTH_SECRET,
  path_user_id: "user_123"
});

// Returns:
// {
//   valid: false,
//   authenticated: false,
//   authorized: false,
//   error: "Authorization header is required",
//   error_code: 401
// }
```

## Integration with Other Components

### With API Endpoints
All API endpoints use jwt_validator as first middleware.

```typescript
// Conceptual API middleware
async function authenticate_middleware(request, next) {
  const validation = await jwt_validator.validate_complete({
    authorization_header: request.headers.get("Authorization"),
    secret: process.env.BETTER_AUTH_SECRET,
    path_user_id: request.params.user_id
  });

  if (!validation.valid) {
    return {
      status: validation.error_code,
      body: {
        error: validation.error_code === 401 ? "Unauthorized" : "Forbidden",
        message: validation.error
      }
    };
  }

  // Attach validated user_id to request
  request.authenticated_user_id = validation.user_id;
  request.jwt_claims = validation.claims;

  // Proceed to next handler
  return next(request);
}

// Chat endpoint
app.post("/api/:user_id/chat", authenticate_middleware, handle_chat);
```

### With Conversation Manager
After authentication, pass validated user_id to conversation operations.

```typescript
// After JWT validation
const user_id = validation.user_id;

// Create conversation
const conversation = await conversation_manager.create_conversation({
  user_id: user_id
});

// Store message
await conversation_manager.store_message({
  conversation_id: conversation.conversation_id,
  user_id: user_id, // Already validated
  role: "user",
  content: message
});
```

### With MCP Validator
Combine with MCP validator for complete request validation.

```typescript
// Full validation flow
async function process_chat_request(request) {
  // Step 1: Authenticate with JWT
  const jwt_validation = await jwt_validator.validate_complete({
    authorization_header: request.headers.get("Authorization"),
    secret: process.env.BETTER_AUTH_SECRET,
    path_user_id: request.params.user_id
  });

  if (!jwt_validation.valid) {
    return auth_error_response(jwt_validation);
  }

  // Step 2: Validate request body
  const body_validation = validate_request_body(request.body);
  if (!body_validation.valid) {
    return {
      status: 400,
      body: { error: "Bad Request", message: body_validation.error }
    };
  }

  // Step 3: Process with MCP tools (validated by mcp_validator)
  const user_id = jwt_validation.user_id;
  const message = body_validation.sanitized_message;

  return process_with_ai(user_id, message);
}
```

## Error Handling Strategy

### HTTP Status Code Mapping

```typescript
{
  // Authentication failures → 401 Unauthorized
  missing_header: 401,
  invalid_format: 401,
  malformed_token: 401,
  invalid_signature: 401,
  expired_token: 401,
  missing_claims: 401,

  // Authorization failures → 403 Forbidden
  user_id_mismatch: 403,

  // Server errors → 500 Internal Server Error
  secret_not_configured: 500,
  validation_exception: 500
}
```

### Error Response Format

**Authentication Error (401):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

**Authorization Error (403):**
```json
{
  "error": "Forbidden",
  "message": "You can only access your own conversations"
}
```

### Logging Strategy

```python
# Conceptual logging
def validate_complete(auth_header, secret, path_user_id):
    try:
        # Extract token
        extraction = extract_token(auth_header)
        if not extraction.valid:
            logger.warning(
                "JWT extraction failed",
                extra={"reason": extraction.error}
            )
            return error_response(401, extraction.error)

        # Verify signature
        signature_check = verify_signature(extraction.token, secret)
        if not signature_check.valid:
            logger.warning(
                "JWT signature verification failed",
                extra={"token_prefix": extraction.token[:20]}
            )
            return error_response(401, "Invalid token signature")

        # Decode claims
        decoded = decode_token(extraction.token)

        # Check expiration
        exp_check = validate_expiration(decoded.claims.exp)
        if not exp_check.valid:
            logger.info(
                "JWT expired",
                extra={
                    "user_id": decoded.claims.user_id,
                    "expired_since": -exp_check.seconds_until_expiry
                }
            )
            return error_response(401, "Token has expired")

        # Validate authorization
        auth_check = validate_user_authorization(
            decoded.claims.user_id,
            path_user_id
        )
        if not auth_check.authorized:
            logger.warning(
                "JWT authorization failed - user_id mismatch",
                extra={
                    "token_user_id": decoded.claims.user_id,
                    "path_user_id": path_user_id
                }
            )
            return error_response(403, auth_check.error)

        # Success
        logger.info(
            "JWT validation successful",
            extra={"user_id": decoded.claims.user_id}
        )
        return success_response(decoded.claims)

    except Exception as e:
        logger.error(
            f"JWT validation exception: {str(e)}",
            exc_info=True
        )
        return error_response(500, "Authentication service error")
```

## Security Considerations

### 1. Secret Management
```python
# ✅ Correct - Load from environment
secret = os.environ.get("BETTER_AUTH_SECRET")
if not secret:
    raise ConfigurationError("BETTER_AUTH_SECRET not configured")

# ❌ Wrong - Never hardcode
secret = "my-secret-key"  # NEVER DO THIS
```

### 2. Constant-Time Comparison
```python
# ✅ Correct - Prevents timing attacks
import hmac
if hmac.compare_digest(signature, expected_signature):
    return True

# ❌ Wrong - Vulnerable to timing attacks
if signature == expected_signature:  # VULNERABLE
    return True
```

### 3. Token Logging
```python
# ✅ Correct - Don't log tokens
logger.info("JWT validation failed", extra={"reason": "expired"})

# ❌ Wrong - Exposes sensitive data
logger.info(f"JWT validation failed: {token}")  # NEVER LOG TOKENS
```

### 4. Error Message Safety
```python
# ✅ Correct - Generic error message
return {"error": "Invalid token signature"}

# ❌ Wrong - Exposes internal details
return {"error": f"HMAC mismatch: expected {expected} got {actual}"}
```

### 5. Clock Skew Tolerance
```python
# ✅ Correct - Allow reasonable clock skew
skew_tolerance = 30  # seconds
if current_time > (exp + skew_tolerance):
    return expired_error()

# ❌ Wrong - Too strict, breaks in distributed systems
if current_time > exp:  # No tolerance
    return expired_error()
```

## Performance Considerations

### Fast Validation
- **Validation Speed:** < 5ms per token (signature verification is main cost)
- **No Network Calls:** All validation is local computation
- **Minimal Overhead:** JWT check adds < 10ms to total request time

### Caching Considerations
```python
# Conceptual - DO NOT cache decoded tokens in memory
# Tokens should be validated fresh on every request

# ❌ Wrong - Security risk
token_cache = {}
def validate(token):
    if token in token_cache:
        return token_cache[token]  # BAD - bypasses expiration check

# ✅ Correct - Always validate fresh
def validate(token, secret):
    # No caching - always verify signature and expiration
    return full_validation_pipeline(token, secret)
```

## Testing Strategy

### Unit Tests
```python
# Conceptual test cases
def test_extract_token_valid_header():
    result = jwt_validator.extract_token({
        "authorization_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    })
    assert result.valid == True
    assert result.token.startswith("eyJ")

def test_extract_token_missing_header():
    result = jwt_validator.extract_token({
        "authorization_header": None
    })
    assert result.valid == False
    assert result.error == "Authorization header is required"

def test_extract_token_wrong_scheme():
    result = jwt_validator.extract_token({
        "authorization_header": "Basic dXNlcjpwYXNz"
    })
    assert result.valid == False
    assert "Bearer" in result.error

def test_verify_signature_valid():
    token = create_valid_test_token()
    secret = "test-secret"
    result = jwt_validator.verify_signature({
        "token": token,
        "secret": secret
    })
    assert result.valid == True

def test_verify_signature_tampered():
    token = create_tampered_test_token()
    secret = "test-secret"
    result = jwt_validator.verify_signature({
        "token": token,
        "secret": secret
    })
    assert result.valid == False
    assert "Invalid token signature" in result.error

def test_validate_expiration_valid():
    future_exp = int(time.time()) + 3600  # 1 hour from now
    result = jwt_validator.validate_expiration({
        "exp": future_exp
    })
    assert result.valid == True
    assert result.expired == False
    assert result.seconds_until_expiry > 0

def test_validate_expiration_expired():
    past_exp = int(time.time()) - 3600  # 1 hour ago
    result = jwt_validator.validate_expiration({
        "exp": past_exp
    })
    assert result.valid == False
    assert result.expired == True
    assert "expired" in result.error.lower()

def test_validate_user_authorization_match():
    result = jwt_validator.validate_user_authorization({
        "token_user_id": "user_123",
        "path_user_id": "user_123"
    })
    assert result.valid == True
    assert result.authorized == True

def test_validate_user_authorization_mismatch():
    result = jwt_validator.validate_user_authorization({
        "token_user_id": "user_123",
        "path_user_id": "user_456"
    })
    assert result.valid == False
    assert result.authorized == False
    assert "own conversations" in result.error

def test_validate_complete_success():
    token = create_valid_test_token(user_id="user_123")
    auth_header = f"Bearer {token}"
    result = jwt_validator.validate_complete({
        "authorization_header": auth_header,
        "secret": "test-secret",
        "path_user_id": "user_123"
    })
    assert result.valid == True
    assert result.authenticated == True
    assert result.authorized == True
    assert result.user_id == "user_123"

def test_validate_complete_expired():
    token = create_expired_test_token()
    auth_header = f"Bearer {token}"
    result = jwt_validator.validate_complete({
        "authorization_header": auth_header,
        "secret": "test-secret",
        "path_user_id": "user_123"
    })
    assert result.valid == False
    assert result.authenticated == False
    assert result.error_code == 401

def test_validate_complete_wrong_user():
    token = create_valid_test_token(user_id="user_123")
    auth_header = f"Bearer {token}"
    result = jwt_validator.validate_complete({
        "authorization_header": auth_header,
        "secret": "test-secret",
        "path_user_id": "user_456"  # Different user!
    })
    assert result.valid == False
    assert result.authenticated == True  # Token is valid
    assert result.authorized == False  # But not authorized
    assert result.error_code == 403
```

### Integration Tests
```python
# Conceptual integration tests with real JWT library
import jwt

def test_real_jwt_validation():
    secret = "test-secret-key"
    user_id = "user_123"

    # Create real JWT
    payload = {
        "user_id": user_id,
        "email": "test@example.com",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    # Validate with our validator
    result = jwt_validator.validate_complete({
        "authorization_header": f"Bearer {token}",
        "secret": secret,
        "path_user_id": user_id
    })

    assert result.valid == True
    assert result.user_id == user_id
    assert result.claims.email == "test@example.com"
```

## Success Metrics

A well-functioning jwt_validator should achieve:

- **Security:** 100% - No unauthorized access, all tokens properly validated
- **Performance:** < 5ms validation time per token
- **Accuracy:** 100% - No false positives or false negatives
- **Error Clarity:** 100% - All validation errors have clear messages with correct HTTP status codes
- **Coverage:** 100% - All authentication and authorization cases handled
- **Reliability:** 99.9%+ - Validator never crashes or causes service failures

## Best Practices

### 1. Always Validate on Every Request
```python
# ✅ Correct - Validate every request
@app.route("/api/<user_id>/chat", methods=["POST"])
def chat_endpoint(user_id):
    validation = jwt_validator.validate_complete(...)
    if not validation.valid:
        return error_response(validation)
    # Proceed

# ❌ Wrong - Skipping validation
@app.route("/api/<user_id>/chat", methods=["POST"])
def chat_endpoint(user_id):
    # No validation - SECURITY VULNERABILITY
    return process_message(user_id)
```

### 2. Use Validated user_id
```python
# ✅ Correct - Use user_id from JWT
validation = jwt_validator.validate_complete(...)
user_id = validation.user_id  # From validated JWT
perform_action(user_id)

# ❌ Wrong - Use user_id from path (not validated)
user_id = request.params.user_id  # Unvalidated!
perform_action(user_id)
```

### 3. Return Appropriate Status Codes
```python
# ✅ Correct - Use error_code from validation
if not validation.valid:
    return {
        "status": validation.error_code,  # 401 or 403
        "body": {"error": validation.error}
    }

# ❌ Wrong - Always return 401
if not validation.valid:
    return {"status": 401, "body": {"error": validation.error}}  # Wrong for 403
```

### 4. Don't Cache Tokens
```python
# ✅ Correct - Always validate fresh
def handle_request(request):
    validation = jwt_validator.validate_complete(...)
    # Fresh validation every time

# ❌ Wrong - Caching tokens
cached_validations = {}
def handle_request(request):
    token = extract_token(request)
    if token in cached_validations:
        return cached_validations[token]  # BAD
```

### 5. Protect Secret
```python
# ✅ Correct - Load from environment
secret = os.environ["BETTER_AUTH_SECRET"]

# ❌ Wrong - Hardcoded or in source control
secret = "hardcoded-secret"  # NEVER
```

## Quality Checklist

Before deploying jwt_validator:

- [ ] Secret loaded from environment variable (BETTER_AUTH_SECRET)
- [ ] Token extraction handles missing/malformed headers
- [ ] Token decoding validates structure (3 parts)
- [ ] Signature verification uses HMAC-SHA256
- [ ] Signature comparison uses constant-time algorithm
- [ ] Expiration check includes clock skew tolerance
- [ ] user_id authorization validates path match
- [ ] Complete validation returns correct HTTP status codes (401 vs 403)
- [ ] Error messages don't expose sensitive information
- [ ] Tokens never logged in plaintext
- [ ] Unit tests cover all validation rules (20+ test cases)
- [ ] Integration tests use real JWT library
- [ ] Performance tested (< 5ms validation time)
- [ ] Security tested (tampered tokens rejected)
- [ ] Documentation complete with examples

---

**This skill ensures all API requests are properly authenticated and authorized before processing!** 🔐
