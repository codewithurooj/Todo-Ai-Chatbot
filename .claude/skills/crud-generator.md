# CRUD Generator Skill

## Purpose
Rapidly generate complete CRUD (Create, Read, Update, Delete) operations following the Todo AI Chatbot's MCP tool architecture, stateless design, and spec-driven development principles. This skill automates the creation of database models, MCP tools, validation schemas, API endpoints, and tests.

## Capabilities
- Generate SQLModel database models with proper constraints
- Create MCP tool definitions with complete schemas
- Generate input/output validation functions
- Create FastAPI endpoint routes with JWT authentication
- Generate unit and integration tests
- Produce comprehensive documentation
- Ensure user isolation and security best practices
- Follow stateless architecture patterns

## Input Parameters
```typescript
{
  entity_name: string;           // Singular form (e.g., "Task", "Note", "Category")
  plural_name?: string;          // Optional (auto-generated if not provided)
  fields: Field[];               // Field definitions
  user_isolated: boolean;        // Whether entity belongs to specific users
  include_timestamps: boolean;   // Add created_at, updated_at fields
  soft_delete: boolean;          // Use deleted_at instead of hard delete
}

interface Field {
  name: string;                  // Field name (snake_case)
  type: 'string' | 'integer' | 'boolean' | 'float' | 'datetime' | 'text';
  required: boolean;
  unique?: boolean;
  min_length?: number;           // For strings
  max_length?: number;           // For strings
  min_value?: number;            // For numbers
  max_value?: number;            // For numbers
  default?: any;
  description: string;           // Used in MCP tool schema
}
```

## Output Structure

The CRUD generator produces a complete package of files:

```
backend/
├── models/
│   └── {entity_name_lower}.py           # SQLModel definition
├── mcp_tools/
│   └── {entity_name_lower}_tools.py     # MCP tool definitions
├── validation/
│   └── {entity_name_lower}_validator.py # Input/output validation
├── routes/
│   └── {entity_name_lower}.py           # FastAPI endpoints
└── tests/
    ├── test_{entity_name_lower}_model.py
    ├── test_{entity_name_lower}_tools.py
    └── test_{entity_name_lower}_api.py
```

## Generated Components

### 1. SQLModel Database Model

**Purpose:** Define the database table schema with proper constraints and relationships.

**Template:**
```python
# models/{entity_name_lower}.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class {EntityName}(SQLModel, table=True):
    """
    {EntityName} model representing {description}.

    This model follows Phase 3 constitution principles:
    - User isolation enforced via user_id
    - Timestamps for audit trail
    - Proper constraints and validations
    """
    __tablename__ = "{entity_name_plural_lower}"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # User isolation (REQUIRED for user-specific entities)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Entity-specific fields
    {field_name}: {field_type} = Field(
        {constraints},
        description="{field_description}"
    )

    # Timestamps (if include_timestamps=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Soft delete (if soft_delete=True)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                {example_fields},
                "created_at": "2025-12-19T10:30:00Z",
                "updated_at": "2025-12-19T10:30:00Z"
            }
        }

# Response models for API
class {EntityName}Create(SQLModel):
    """Schema for creating new {entity_name}"""
    user_id: int
    {create_fields}

class {EntityName}Update(SQLModel):
    """Schema for updating {entity_name}"""
    {update_fields}  # All optional

class {EntityName}Response(SQLModel):
    """Schema for {entity_name} responses"""
    id: int
    user_id: int
    {response_fields}
    created_at: datetime
    updated_at: datetime
```

### 2. MCP Tool Definitions

**Purpose:** Create MCP tools for all CRUD operations following the Official MCP SDK patterns.

**Template:**
```python
# mcp_tools/{entity_name_lower}_tools.py
from mcp.server.models import Tool
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from models.{entity_name_lower} import {EntityName}
from database import get_session

# Tool input schemas
class Add{EntityName}Input(BaseModel):
    """Input schema for add_{entity_name_lower} tool"""
    user_id: int = Field(..., description="ID of the user creating the {entity_name}")
    {input_fields}

class List{EntityName}sInput(BaseModel):
    """Input schema for list_{entity_name_plural_lower} tool"""
    user_id: int = Field(..., description="ID of the user")
    {filter_fields}  # Optional filters (e.g., completed, category_id)

class Update{EntityName}Input(BaseModel):
    """Input schema for update_{entity_name_lower} tool"""
    user_id: int = Field(..., description="ID of the user")
    {entity_name_lower}_id: int = Field(..., description="ID of the {entity_name} to update")
    {update_fields}  # All optional

class Delete{EntityName}Input(BaseModel):
    """Input schema for delete_{entity_name_lower} tool"""
    user_id: int = Field(..., description="ID of the user")
    {entity_name_lower}_id: int = Field(..., description="ID of the {entity_name} to delete")

# MCP Tools
async def add_{entity_name_lower}(user_id: int, {params}) -> Dict[str, Any]:
    """
    Add a new {entity_name} for a user.

    Args:
        user_id: ID of the user creating the {entity_name}
        {param_descriptions}

    Returns:
        Dict containing success status and created {entity_name}
    """
    async with get_session() as session:
        # Create {entity_name}
        {entity_name_var} = {EntityName}(
            user_id=user_id,
            {field_assignments}
        )

        session.add({entity_name_var})
        await session.commit()
        await session.refresh({entity_name_var})

        return {
            "success": True,
            "{entity_name_lower}": {entity_name_var}.dict()
        }

async def list_{entity_name_plural_lower}(user_id: int, {filters}) -> Dict[str, Any]:
    """
    List all {entity_name_plural_lower} for a user.

    Args:
        user_id: ID of the user
        {filter_descriptions}

    Returns:
        Dict containing success status, {entity_name_plural_lower} list, and count
    """
    async with get_session() as session:
        # Build query with user isolation
        query = select({EntityName}).where(
            {EntityName}.user_id == user_id
        )

        # Apply filters
        {filter_logic}

        # Apply soft delete filter
        if not include_deleted:
            query = query.where({EntityName}.deleted_at.is_(None))

        # Execute query
        result = await session.execute(query)
        {entity_name_plural_var} = result.scalars().all()

        return {
            "success": True,
            "{entity_name_plural_lower}": [{entity_name_var}.dict() for {entity_name_var} in {entity_name_plural_var}],
            "count": len({entity_name_plural_var})
        }

async def update_{entity_name_lower}(
    user_id: int,
    {entity_name_lower}_id: int,
    {update_params}
) -> Dict[str, Any]:
    """
    Update an existing {entity_name}.

    Args:
        user_id: ID of the user
        {entity_name_lower}_id: ID of the {entity_name} to update
        {update_param_descriptions}

    Returns:
        Dict containing success status and updated {entity_name}
    """
    async with get_session() as session:
        # Find {entity_name} with user isolation
        query = select({EntityName}).where(
            {EntityName}.id == {entity_name_lower}_id,
            {EntityName}.user_id == user_id
        )
        result = await session.execute(query)
        {entity_name_var} = result.scalar_one_or_none()

        if not {entity_name_var}:
            return {
                "success": False,
                "error": "{EntityName} not found or access denied"
            }

        # Update fields
        {update_logic}

        # Update timestamp
        {entity_name_var}.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh({entity_name_var})

        return {
            "success": True,
            "{entity_name_lower}": {entity_name_var}.dict()
        }

async def delete_{entity_name_lower}(
    user_id: int,
    {entity_name_lower}_id: int
) -> Dict[str, Any]:
    """
    Delete a {entity_name} (soft delete if enabled, otherwise hard delete).

    Args:
        user_id: ID of the user
        {entity_name_lower}_id: ID of the {entity_name} to delete

    Returns:
        Dict containing success status and deletion confirmation
    """
    async with get_session() as session:
        # Find {entity_name} with user isolation
        query = select({EntityName}).where(
            {EntityName}.id == {entity_name_lower}_id,
            {EntityName}.user_id == user_id
        )
        result = await session.execute(query)
        {entity_name_var} = result.scalar_one_or_none()

        if not {entity_name_var}:
            return {
                "success": False,
                "error": "{EntityName} not found or access denied"
            }

        # Soft delete or hard delete
        if {soft_delete}:
            {entity_name_var}.deleted_at = datetime.utcnow()
            await session.commit()
            message = "{EntityName} soft deleted successfully"
        else:
            await session.delete({entity_name_var})
            await session.commit()
            message = "{EntityName} deleted successfully"

        return {
            "success": True,
            "message": message,
            "deleted_{entity_name_lower}_id": {entity_name_lower}_id
        }

# MCP Tool Registration
TOOLS = [
    Tool(
        name="add_{entity_name_lower}",
        description="Add a new {entity_name} for a user",
        inputSchema=Add{EntityName}Input.schema()
    ),
    Tool(
        name="list_{entity_name_plural_lower}",
        description="List all {entity_name_plural_lower} for a user with optional filters",
        inputSchema=List{EntityName}sInput.schema()
    ),
    Tool(
        name="update_{entity_name_lower}",
        description="Update an existing {entity_name}",
        inputSchema=Update{EntityName}Input.schema()
    ),
    Tool(
        name="delete_{entity_name_lower}",
        description="Delete a {entity_name}",
        inputSchema=Delete{EntityName}Input.schema()
    ),
]
```

### 3. Input/Output Validation

**Purpose:** Validate all MCP tool inputs and outputs following security best practices.

**Template:**
```python
# validation/{entity_name_lower}_validator.py
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

class {EntityName}Validator:
    """
    Validator for {entity_name} MCP tool inputs and outputs.

    Follows Phase 3 constitution principles:
    - Validates all inputs before tool execution
    - Validates all outputs before returning to client
    - Enforces security constraints (user_id, injection prevention)
    - Provides clear error messages
    """

    # Validation rules
    VALID_TOOLS = [
        "add_{entity_name_lower}",
        "list_{entity_name_plural_lower}",
        "update_{entity_name_lower}",
        "delete_{entity_name_lower}"
    ]

    {FIELD_CONSTRAINTS}

    @staticmethod
    def validate_user_id(user_id: Any) -> tuple[bool, Optional[str]]:
        """Validate user_id is present and valid"""
        if user_id is None:
            return False, "user_id is required"

        if not isinstance(user_id, int):
            return False, "user_id must be an integer"

        if user_id < 1:
            return False, "user_id must be positive"

        return True, None

    @staticmethod
    def validate_string_field(
        value: Any,
        field_name: str,
        required: bool,
        min_length: int = 1,
        max_length: int = 500
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Validate string field with length constraints"""
        # Check required
        if value is None or value == "":
            if required:
                return False, f"{field_name} is required and cannot be empty", None
            return True, None, None

        # Check type
        if not isinstance(value, str):
            return False, f"{field_name} must be a string", None

        # Check for null bytes (security)
        if '\x00' in value:
            return False, f"{field_name} contains invalid null bytes", None

        # Check length
        if len(value) < min_length:
            return False, f"{field_name} must be at least {min_length} characters", None

        if len(value) > max_length:
            return False, f"{field_name} must be {max_length} characters or less", None

        # Check for SQL injection patterns
        dangerous_patterns = ['--', ';--', '/*', '*/', 'UNION', 'SELECT', 'DROP', 'INSERT', 'DELETE']
        value_upper = value.upper()
        for pattern in dangerous_patterns:
            if pattern in value_upper:
                return False, "Invalid input detected", None

        # Sanitize
        sanitized = value.strip()

        return True, None, sanitized

    @staticmethod
    def validate_integer_field(
        value: Any,
        field_name: str,
        required: bool,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate integer field with range constraints"""
        # Check required
        if value is None:
            if required:
                return False, f"{field_name} is required"
            return True, None

        # Check type
        if not isinstance(value, int):
            return False, f"{field_name} must be an integer"

        # Check range
        if min_value is not None and value < min_value:
            return False, f"{field_name} must be at least {min_value}"

        if max_value is not None and value > max_value:
            return False, f"{field_name} must be at most {max_value}"

        return True, None

    @classmethod
    def validate_add_{entity_name_lower}_input(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate add_{entity_name_lower} tool input"""
        errors = []
        sanitized = {}

        # Validate user_id
        valid, error = cls.validate_user_id(parameters.get("user_id"))
        if not valid:
            errors.append(error)
        else:
            sanitized["user_id"] = parameters["user_id"]

        # Validate each field
        {FIELD_VALIDATIONS}

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "sanitized_parameters": sanitized}

    @classmethod
    def validate_list_{entity_name_plural_lower}_input(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate list_{entity_name_plural_lower} tool input"""
        errors = []
        sanitized = {}

        # Validate user_id
        valid, error = cls.validate_user_id(parameters.get("user_id"))
        if not valid:
            errors.append(error)
        else:
            sanitized["user_id"] = parameters["user_id"]

        # Validate optional filters
        {FILTER_VALIDATIONS}

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "sanitized_parameters": sanitized}

    @classmethod
    def validate_update_{entity_name_lower}_input(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate update_{entity_name_lower} tool input"""
        errors = []
        sanitized = {}

        # Validate user_id
        valid, error = cls.validate_user_id(parameters.get("user_id"))
        if not valid:
            errors.append(error)
        else:
            sanitized["user_id"] = parameters["user_id"]

        # Validate {entity_name_lower}_id
        valid, error = cls.validate_integer_field(
            parameters.get("{entity_name_lower}_id"),
            "{entity_name_lower}_id",
            required=True,
            min_value=1
        )
        if not valid:
            errors.append(error)
        else:
            sanitized["{entity_name_lower}_id"] = parameters["{entity_name_lower}_id"]

        # At least one update field required
        update_fields = {UPDATE_FIELD_LIST}
        provided_updates = [f for f in update_fields if parameters.get(f) is not None]

        if not provided_updates:
            errors.append("At least one field must be provided for update")

        # Validate provided update fields
        {UPDATE_FIELD_VALIDATIONS}

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "sanitized_parameters": sanitized}

    @classmethod
    def validate_delete_{entity_name_lower}_input(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate delete_{entity_name_lower} tool input"""
        errors = []
        sanitized = {}

        # Validate user_id
        valid, error = cls.validate_user_id(parameters.get("user_id"))
        if not valid:
            errors.append(error)
        else:
            sanitized["user_id"] = parameters["user_id"]

        # Validate {entity_name_lower}_id
        valid, error = cls.validate_integer_field(
            parameters.get("{entity_name_lower}_id"),
            "{entity_name_lower}_id",
            required=True,
            min_value=1
        )
        if not valid:
            errors.append(error)
        else:
            sanitized["{entity_name_lower}_id"] = parameters["{entity_name_lower}_id"]

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "sanitized_parameters": sanitized}

    @staticmethod
    def validate_output(tool_name: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool output response"""
        errors = []

        # Check success field
        if "success" not in response:
            errors.append("Response missing required field: success")
        elif not isinstance(response["success"], bool):
            errors.append("Response field 'success' must be boolean")

        # If success=True, validate specific response structure
        if response.get("success"):
            if tool_name in ["add_{entity_name_lower}", "update_{entity_name_lower}"]:
                if "{entity_name_lower}" not in response:
                    errors.append("Response missing required field: {entity_name_lower}")
                else:
                    # Validate {entity_name_lower} object structure
                    {entity_name_var} = response["{entity_name_lower}"]
                    required_fields = ["id", "user_id", {REQUIRED_RESPONSE_FIELDS}]
                    for field in required_fields:
                        if field not in {entity_name_var}:
                            errors.append(f"{entity_name_lower} missing required field: {field}")

            elif tool_name == "list_{entity_name_plural_lower}":
                if "{entity_name_plural_lower}" not in response:
                    errors.append("Response missing required field: {entity_name_plural_lower}")
                elif not isinstance(response["{entity_name_plural_lower}"], list):
                    errors.append("{entity_name_plural_lower} must be an array")

                if "count" not in response:
                    errors.append("Response missing required field: count")

            elif tool_name == "delete_{entity_name_lower}":
                if "deleted_{entity_name_lower}_id" not in response:
                    errors.append("Response missing required field: deleted_{entity_name_lower}_id")

        # If success=False, validate error message
        if response.get("success") is False:
            if "error" not in response:
                errors.append("Error response missing 'error' field")
            elif not isinstance(response["error"], str) or not response["error"]:
                errors.append("Error message must be non-empty string")

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "validated_response": response}
```

### 4. FastAPI Endpoint Routes

**Purpose:** Create REST API endpoints with JWT authentication and proper error handling.

**Template:**
```python
# routes/{entity_name_lower}.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from models.{entity_name_lower} import {EntityName}, {EntityName}Create, {EntityName}Update, {EntityName}Response
from mcp_tools.{entity_name_lower}_tools import (
    add_{entity_name_lower},
    list_{entity_name_plural_lower},
    update_{entity_name_lower},
    delete_{entity_name_lower}
)
from validation.{entity_name_lower}_validator import {EntityName}Validator
from auth import verify_jwt_token

router = APIRouter(
    prefix="/api/{{user_id}}/{entity_name_plural_lower}",
    tags=["{entity_name_plural_lower}"]
)

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Extract and verify user_id from JWT token"""
    token = credentials.credentials
    user_id = verify_jwt_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return user_id

@router.post("/", response_model={EntityName}Response, status_code=status.HTTP_201_CREATED)
async def create_{entity_name_lower}(
    user_id: int,
    {entity_name_var}_data: {EntityName}Create,
    current_user: int = Depends(get_current_user)
):
    """
    Create a new {entity_name}.

    - **user_id**: ID of the user (from path)
    - **{field_list}**: {entity_name} fields

    Returns the created {entity_name} with ID and timestamps.
    """
    # Verify user_id from path matches authenticated user
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create {entity_name_lower} for other users"
        )

    # Validate input
    validation_result = {EntityName}Validator.validate_add_{entity_name_lower}_input(
        {entity_name_var}_data.dict()
    )

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_result["errors"]}
        )

    # Call MCP tool
    result = await add_{entity_name_lower}(**validation_result["sanitized_parameters"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to create {entity_name_lower}")
        )

    return result["{entity_name_lower}"]

@router.get("/", response_model=List[{EntityName}Response])
async def get_{entity_name_plural_lower}(
    user_id: int,
    {filter_params},
    current_user: int = Depends(get_current_user)
):
    """
    List all {entity_name_plural_lower} for a user.

    - **user_id**: ID of the user (from path)
    - **{filter_descriptions}**: Optional filters

    Returns list of {entity_name_plural_lower}.
    """
    # Verify user_id from path matches authenticated user
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' {entity_name_plural_lower}"
        )

    # Validate input
    params = {"user_id": user_id, {filter_param_dict}}
    validation_result = {EntityName}Validator.validate_list_{entity_name_plural_lower}_input(params)

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_result["errors"]}
        )

    # Call MCP tool
    result = await list_{entity_name_plural_lower}(**validation_result["sanitized_parameters"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to list {entity_name_plural_lower}")
        )

    return result["{entity_name_plural_lower}"]

@router.get("/{{id}}", response_model={EntityName}Response)
async def get_{entity_name_lower}_by_id(
    user_id: int,
    id: int,
    current_user: int = Depends(get_current_user)
):
    """
    Get a specific {entity_name} by ID.

    - **user_id**: ID of the user (from path)
    - **id**: ID of the {entity_name}

    Returns the {entity_name} if found and owned by user.
    """
    # Verify user_id from path matches authenticated user
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' {entity_name_plural_lower}"
        )

    # Use list tool with filter
    result = await list_{entity_name_plural_lower}(user_id=user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to retrieve {entity_name_lower}")
        )

    # Find {entity_name} by ID
    {entity_name_var} = next(
        (item for item in result["{entity_name_plural_lower}"] if item["id"] == id),
        None
    )

    if not {entity_name_var}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{EntityName} not found"
        )

    return {entity_name_var}

@router.patch("/{{id}}", response_model={EntityName}Response)
async def update_{entity_name_lower}_endpoint(
    user_id: int,
    id: int,
    {entity_name_var}_data: {EntityName}Update,
    current_user: int = Depends(get_current_user)
):
    """
    Update an existing {entity_name}.

    - **user_id**: ID of the user (from path)
    - **id**: ID of the {entity_name} to update
    - **{field_list}**: Fields to update (all optional)

    Returns the updated {entity_name}.
    """
    # Verify user_id from path matches authenticated user
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other users' {entity_name_plural_lower}"
        )

    # Validate input
    params = {
        "user_id": user_id,
        "{entity_name_lower}_id": id,
        **{entity_name_var}_data.dict(exclude_unset=True)
    }
    validation_result = {EntityName}Validator.validate_update_{entity_name_lower}_input(params)

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_result["errors"]}
        )

    # Call MCP tool
    result = await update_{entity_name_lower}(**validation_result["sanitized_parameters"])

    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to update {entity_name_lower}")
        )

    return result["{entity_name_lower}"]

@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{entity_name_lower}_endpoint(
    user_id: int,
    id: int,
    current_user: int = Depends(get_current_user)
):
    """
    Delete a {entity_name}.

    - **user_id**: ID of the user (from path)
    - **id**: ID of the {entity_name} to delete

    Returns 204 No Content on success.
    """
    # Verify user_id from path matches authenticated user
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other users' {entity_name_plural_lower}"
        )

    # Validate input
    params = {"user_id": user_id, "{entity_name_lower}_id": id}
    validation_result = {EntityName}Validator.validate_delete_{entity_name_lower}_input(params)

    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_result["errors"]}
        )

    # Call MCP tool
    result = await delete_{entity_name_lower}(**validation_result["sanitized_parameters"])

    if not result["success"]:
        if "not found" in result.get("error", "").lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to delete {entity_name_lower}")
        )

    return None
```

### 5. Unit Tests

**Purpose:** Comprehensive test coverage for models, tools, validators, and API endpoints.

**Template:**
```python
# tests/test_{entity_name_lower}_model.py
import pytest
from models.{entity_name_lower} import {EntityName}
from datetime import datetime

def test_create_{entity_name_lower}_with_all_fields():
    """{EntityName} can be created with all fields"""
    {entity_name_var} = {EntityName}(
        user_id=123,
        {test_field_assignments}
    )

    assert {entity_name_var}.user_id == 123
    {test_field_assertions}
    assert isinstance({entity_name_var}.created_at, datetime)
    assert isinstance({entity_name_var}.updated_at, datetime)

def test_{entity_name_lower}_timestamps_auto_set():
    """Timestamps are automatically set on creation"""
    {entity_name_var} = {EntityName}(user_id=123, {minimal_fields})

    assert {entity_name_var}.created_at is not None
    assert {entity_name_var}.updated_at is not None
    assert {entity_name_var}.created_at == {entity_name_var}.updated_at

# tests/test_{entity_name_lower}_validator.py
import pytest
from validation.{entity_name_lower}_validator import {EntityName}Validator

def test_validate_add_{entity_name_lower}_valid_input():
    """Valid input passes validation"""
    params = {
        "user_id": 123,
        {valid_test_params}
    }

    result = {EntityName}Validator.validate_add_{entity_name_lower}_input(params)

    assert result["valid"] is True
    assert "sanitized_parameters" in result

def test_validate_add_{entity_name_lower}_missing_required_field():
    """Missing required field fails validation"""
    params = {"user_id": 123}  # Missing required fields

    result = {EntityName}Validator.validate_add_{entity_name_lower}_input(params)

    assert result["valid"] is False
    assert len(result["errors"]) > 0

def test_validate_update_{entity_name_lower}_no_fields_provided():
    """Update with no fields fails validation"""
    params = {
        "user_id": 123,
        "{entity_name_lower}_id": 10
    }

    result = {EntityName}Validator.validate_update_{entity_name_lower}_input(params)

    assert result["valid"] is False
    assert "at least one field" in result["errors"][0].lower()

# tests/test_{entity_name_lower}_tools.py
import pytest
from mcp_tools.{entity_name_lower}_tools import (
    add_{entity_name_lower},
    list_{entity_name_plural_lower},
    update_{entity_name_lower},
    delete_{entity_name_lower}
)

@pytest.mark.asyncio
async def test_add_{entity_name_lower}_success():
    """Adding {entity_name_lower} returns success with created {entity_name_lower}"""
    result = await add_{entity_name_lower}(
        user_id=123,
        {test_tool_params}
    )

    assert result["success"] is True
    assert "{entity_name_lower}" in result
    assert result["{entity_name_lower}"]["user_id"] == 123

@pytest.mark.asyncio
async def test_list_{entity_name_plural_lower}_user_isolation():
    """User can only see their own {entity_name_plural_lower}"""
    # Create {entity_name_lower} for user 123
    await add_{entity_name_lower}(user_id=123, {test_params})

    # Create {entity_name_lower} for user 456
    await add_{entity_name_lower}(user_id=456, {test_params})

    # List for user 123
    result = await list_{entity_name_plural_lower}(user_id=123)

    # Should only see {entity_name_plural_lower} for user 123
    assert all({entity_name_var}["user_id"] == 123 for {entity_name_var} in result["{entity_name_plural_lower}"])

@pytest.mark.asyncio
async def test_update_{entity_name_lower}_not_found():
    """Updating non-existent {entity_name_lower} fails"""
    result = await update_{entity_name_lower}(
        user_id=123,
        {entity_name_lower}_id=99999,  # Doesn't exist
        {update_params}
    )

    assert result["success"] is False
    assert "not found" in result["error"].lower()

@pytest.mark.asyncio
async def test_delete_{entity_name_lower}_success():
    """Deleting {entity_name_lower} returns success"""
    # Create {entity_name_lower}
    add_result = await add_{entity_name_lower}(user_id=123, {test_params})
    {entity_name_lower}_id = add_result["{entity_name_lower}"]["id"]

    # Delete {entity_name_lower}
    delete_result = await delete_{entity_name_lower}(user_id=123, {entity_name_lower}_id={entity_name_lower}_id)

    assert delete_result["success"] is True
    assert delete_result["deleted_{entity_name_lower}_id"] == {entity_name_lower}_id

# tests/test_{entity_name_lower}_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_{entity_name_lower}_endpoint():
    """POST /{entity_name_plural_lower} creates new {entity_name_lower}"""
    response = client.post(
        "/api/123/{entity_name_plural_lower}/",
        json={test_api_body},
        headers={"Authorization": "Bearer valid_token"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 123

def test_get_{entity_name_plural_lower}_endpoint():
    """GET /{entity_name_plural_lower} returns list"""
    response = client.get(
        "/api/123/{entity_name_plural_lower}/",
        headers={"Authorization": "Bearer valid_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_{entity_name_lower}_endpoint():
    """PATCH /{entity_name_plural_lower}/{{id}} updates {entity_name_lower}"""
    # First create {entity_name_lower}
    create_response = client.post(...)
    {entity_name_lower}_id = create_response.json()["id"]

    # Update {entity_name_lower}
    response = client.patch(
        f"/api/123/{entity_name_plural_lower}/{{{entity_name_lower}_id}}",
        json={update_api_body},
        headers={"Authorization": "Bearer valid_token"}
    )

    assert response.status_code == 200

def test_delete_{entity_name_lower}_endpoint():
    """DELETE /{entity_name_plural_lower}/{{id}} deletes {entity_name_lower}"""
    # First create {entity_name_lower}
    create_response = client.post(...)
    {entity_name_lower}_id = create_response.json()["id"]

    # Delete {entity_name_lower}
    response = client.delete(
        f"/api/123/{entity_name_plural_lower}/{{{entity_name_lower}_id}}",
        headers={"Authorization": "Bearer valid_token"}
    )

    assert response.status_code == 204
```

## Usage Examples

### Example 1: Generate CRUD for "Category" Entity

```markdown
**User**: Use the CRUD generator skill to create CRUD operations for a Category entity.

**Claude**: I'll generate complete CRUD operations for the Category entity.

**Input:**
```typescript
{
  entity_name: "Category",
  plural_name: "Categories",
  fields: [
    {
      name: "name",
      type: "string",
      required: true,
      unique: true,
      min_length: 1,
      max_length: 100,
      description: "Category name (e.g., Work, Personal, Shopping)"
    },
    {
      name: "color",
      type: "string",
      required: false,
      max_length: 7,
      description: "Hex color code for UI (e.g., #FF5733)"
    },
    {
      name: "icon",
      type: "string",
      required: false,
      max_length: 50,
      description: "Icon name or emoji for UI"
    }
  ],
  user_isolated: true,
  include_timestamps: true,
  soft_delete: true
}
```

**Output:**
Generated files:
- `models/category.py` - SQLModel with name, color, icon fields
- `mcp_tools/category_tools.py` - 4 MCP tools (add, list, update, delete)
- `validation/category_validator.py` - Input/output validation
- `routes/category.py` - 5 FastAPI endpoints with JWT auth
- `tests/test_category_*.py` - 30+ test cases

**Summary:**
Created complete CRUD system for Categories with:
- User isolation (users can only manage their own categories)
- Unique constraint on category name per user
- Soft delete (deleted_at field)
- Color and icon support for UI
- Full validation and security checks
```

### Example 2: Generate CRUD for "Note" Entity

```markdown
**Input:**
```typescript
{
  entity_name: "Note",
  fields: [
    {
      name: "title",
      type: "string",
      required: true,
      max_length: 200,
      description: "Note title"
    },
    {
      name: "content",
      type: "text",
      required: true,
      max_length: 10000,
      description: "Note content (supports markdown)"
    },
    {
      name: "category_id",
      type: "integer",
      required: false,
      min_value: 1,
      description: "Optional category ID for organization"
    },
    {
      name: "pinned",
      type: "boolean",
      required: false,
      default: false,
      description: "Whether note is pinned to top"
    }
  ],
  user_isolated: true,
  include_timestamps: true,
  soft_delete: false
}
```

**Output:**
Generated files with:
- Text field for large content (10,000 char limit)
- Optional category relationship
- Pinned flag for UI prioritization
- Hard delete (no soft delete)
- List filtering by category_id and pinned status
```

## Best Practices

### 1. Always Include User Isolation
```typescript
// ✅ Correct
{
  entity_name: "Task",
  user_isolated: true  // User-specific entities
}

// ❌ Wrong (unless truly global data)
{
  entity_name: "Task",
  user_isolated: false
}
```

### 2. Use Soft Delete for Important Data
```typescript
// ✅ Correct - Preserves data for recovery
{
  entity_name: "Task",
  soft_delete: true
}

// ⚠️ Use with caution - Permanent deletion
{
  entity_name: "Task",
  soft_delete: false
}
```

### 3. Define Clear Field Constraints
```typescript
// ✅ Correct - Explicit constraints
{
  name: "email",
  type: "string",
  required: true,
  unique: true,
  max_length: 320,  // RFC 5321 email length limit
  description: "User email address"
}

// ❌ Wrong - Missing constraints
{
  name: "email",
  type: "string"
}
```

### 4. Include Timestamps for Audit Trail
```typescript
// ✅ Correct
{
  include_timestamps: true  // Enables created_at, updated_at
}

// ❌ Wrong (unless timestamps truly not needed)
{
  include_timestamps: false
}
```

### 5. Provide Clear Descriptions
```typescript
// ✅ Correct - Used in API docs and MCP schemas
{
  name: "priority",
  type: "integer",
  description: "Task priority level (1=Low, 2=Medium, 3=High)"
}

// ❌ Wrong - No description
{
  name: "priority",
  type: "integer"
}
```

## Quality Checklist

Generated CRUD operations should have:

- [ ] SQLModel with proper table name and constraints
- [ ] User isolation enforced (if user_isolated=true)
- [ ] All 4 MCP tools (add, list, update, delete) with schemas
- [ ] Input validation for all tool parameters
- [ ] Output validation for all tool responses
- [ ] Security checks (SQL injection prevention, null byte filtering)
- [ ] 5 FastAPI endpoints (POST, GET list, GET by ID, PATCH, DELETE)
- [ ] JWT authentication on all endpoints
- [ ] User authorization checks (user can only access their own data)
- [ ] Proper HTTP status codes (201, 200, 204, 400, 404, 403, 500)
- [ ] 30+ unit tests covering all operations
- [ ] Integration tests for API endpoints
- [ ] Clear error messages
- [ ] Timestamps (if include_timestamps=true)
- [ ] Soft delete logic (if soft_delete=true)
- [ ] Documentation comments in all files

## Success Metrics

A well-generated CRUD system should achieve:

- **Code Quality:** Follows all Phase 3 constitution principles
- **Security:** 100% user isolation enforcement, injection prevention
- **Test Coverage:** 80%+ code coverage
- **Performance:** < 100ms for CRUD operations (p95)
- **Completeness:** All 4 operations functional out-of-the-box
- **Documentation:** Clear API docs, inline comments
- **Maintainability:** Easy to extend with additional fields

## Integration with Development Workflow

This skill integrates with:

1. **Spec-Driven Development:** Generate CRUD from spec requirements
2. **MCP Architecture:** All operations exposed as MCP tools
3. **Stateless Design:** No in-memory state, all data in database
4. **JWT Authentication:** All endpoints require valid tokens
5. **Constitution Principles:** Enforces all Phase 3 requirements

## Time Efficiency

- **Manual CRUD creation:** 4-6 hours per entity
- **With this skill:** 5-10 minutes per entity
- **Time saved:** 95%+

## Reusability

Use this skill for:
- Task management entities (Category, Tag, Priority)
- Note-taking entities (Note, Notebook, Attachment)
- Any user-specific data entities
- Admin entities (Settings, Preferences)
- Relational entities (TaskComment, TaskAttachment)

---

**This skill makes CRUD development effortless while maintaining all architectural principles!** 🚀
