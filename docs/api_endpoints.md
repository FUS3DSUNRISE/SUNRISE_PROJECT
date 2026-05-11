# API Endpoints Documentation

## Overview

This document describes the REST API endpoints provided by the backend of the 3D asset generation system.

The API allows users to:

- create and manage accounts
- submit 3D generation prompts
- track asynchronous generation status
- download generated GLB files
- import existing 3D assets
- modify generated or imported assets
- submit feedback on generated results
- access analytics and CSV exports for evaluation

The backend uses session-based authentication. After login or signup, the user ID is stored in the Flask session and reused to protect private resources.

---

## Base URL

For local development:

```http
http://localhost:5000
```

---

## Root Endpoint

### Health Check / API Status

```http
GET /
```

Returns a simple message to confirm that the API is running.

### Success Response

```txt
API is running
```

---

## Authentication

Authentication is based on Flask sessions.

After a successful signup or login, the backend stores the authenticated user ID in the session:

```python
session["user_id"] = user.id
```

Protected endpoints check whether `user_id` exists in the session before allowing access.

If the user is not authenticated, the API usually returns:

```json
{
  "error": "Not authenticated"
}
```

or:

```json
{
  "status": "error",
  "message": "Not authenticated"
}
```

---

# 1. Authentication Endpoints

The authentication endpoints are defined in `auth.py`.

Base prefix:

```http
/auth
```

---

## 1.1 Signup

```http
POST /auth/signup
```

Creates a new user account.

### Authentication

Not required.

### Request Body

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Behavior

The backend:

1. Checks that the request body exists.
2. Validates that email and password are provided.
3. Checks if the email is already used.
4. Generates a username from the email prefix.
5. Hashes the password.
6. Creates the user in the database.
7. Stores the user ID in the session.

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "message": "Signup successful",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com"
  }
}
```

### Error Responses

Missing JSON body:

```http
400 Bad Request
```

```json
{
  "error": "Missing JSON body"
}
```

Missing email or password:

```http
400 Bad Request
```

```json
{
  "error": "Email and password are required"
}
```

Email already used:

```http
409 Conflict
```

```json
{
  "error": "Email already in use"
}
```

---

## 1.2 Login

```http
POST /auth/login
```

Logs in an existing user.

### Authentication

Not required.

### Request Body

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Behavior

The backend:

1. Checks that the request body exists.
2. Validates that email and password are provided.
3. Searches for the user by email.
4. Checks the password hash.
5. Stores the user ID in the session.

### Success Response

Status code:

```http
200 OK
```

Response:

```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com"
  }
}
```

### Error Responses

Missing JSON body:

```http
400 Bad Request
```

```json
{
  "error": "Missing JSON body"
}
```

Missing email or password:

```http
400 Bad Request
```

```json
{
  "error": "Email and password are required"
}
```

Invalid credentials:

```http
401 Unauthorized
```

```json
{
  "error": "Invalid credentials"
}
```

---

## 1.3 Get Current User

```http
GET /auth/me
```

Returns the currently authenticated user.

### Authentication

Required.

### Success Response

Status code:

```http
200 OK
```

Response:

```json
{
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com"
  }
}
```

### Error Responses

User not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

User not found:

```http
404 Not Found
```

```json
{
  "error": "User not found"
}
```

---

## 1.4 Logout

```http
POST /auth/logout
```

Logs out the current user by removing `user_id` from the session.

### Authentication

Not strictly required, but usually called by an authenticated user.

### Success Response

Status code:

```http
200 OK
```

Response:

```json
{
  "message": "Logout successful"
}
```

---

# 2. Prompt Endpoints

The prompt endpoints are defined in `prompts.py`.

Base prefix:

```http
/prompts
```

These endpoints manage prompt submission, generation status, file access, modification, feedback, analytics and export.

---

## 2.1 Create Prompt

```http
POST /prompts
```

Creates a new prompt request and starts the asynchronous 3D generation process.

### Authentication

Required.

### Request Body

```json
{
  "prompt": "Create a modern wooden chair",
  "parameters": {
    "size": "medium",
    "material": "wood",
    "style": "modern"
  }
}
```

The `parameters` field is optional.

### Behavior

The backend:

1. Checks if the user is authenticated.
2. Reads the prompt from the JSON body.
3. Validates optional parameters using the `Parameters` schema.
4. Checks that the user exists.
5. Classifies the prompt intent using the LLM.
6. Depending on the classification:
   - blocks unsafe or invalid requests
   - asks for clarification
   - proceeds with generation
7. Creates a `PromptRequest` with status `QUEUED`.
8. Sends the task to Celery using `process_prompt_task.delay(...)`.

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "id": 1,
  "prompt": "Create a modern wooden chair",
  "status": "QUEUED",
  "user_id": 1,
  "created_at": "2026-05-11T10:30:00+00:00"
}
```

### Clarification Response

If the prompt needs clarification, the API creates a prompt with status `AWAITING_CLARIFICATION`.

Status code:

```http
200 OK
```

Response:

```json
{
  "id": 1,
  "status": "clarify",
  "message": "The prompt needs more details.",
  "created_at": "2026-05-11T10:30:00+00:00"
}
```

### Error Responses

User not authenticated:

```http
401 Unauthorized
```

```json
{
  "status": "error",
  "message": "Not authenticated"
}
```

Missing prompt:

```http
400 Bad Request
```

```json
{
  "status": "error",
  "message": "Missing prompt"
}
```

User not found:

```http
404 Not Found
```

```json
{
  "status": "error",
  "message": "User not found"
}
```

Blocked request:

```http
400 Bad Request
```

```json
{
  "status": "error",
  "message": "Reason returned by the classifier"
}
```

Invalid parameters:

```http
400 Bad Request
```

```json
{
  "error": "Validation error message"
}
```

---

## 2.2 Get Prompt by ID

```http
GET /prompts/{id}
```

Returns details about a specific prompt, including its status, result path and version history.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Prompt ID |

### Behavior

The backend:

1. Retrieves the prompt by ID.
2. Checks if the user is authenticated.
3. Checks if the prompt belongs to the authenticated user.
4. Builds the version history from the root prompt.
5. Returns prompt details.

### Success Response

Status code:

```http
200 OK
```

Response:

```json
{
  "id": 1,
  "prompt": "Create a modern wooden chair",
  "status": "COMPLETED",
  "result_path": "static/models/result.glb",
  "error_message": null,
  "user_id": 1,
  "username": "user",
  "parent_prompt_id": null,
  "modification_command": null,
  "root_prompt_id": 1,
  "created_at": "2026-05-11T10:30:00+00:00",
  "version_history": [
    {
      "id": 1,
      "parent_prompt_id": null,
      "prompt": "Create a modern wooden chair",
      "modification_command": null,
      "status": "COMPLETED",
      "result_path": "static/models/result.glb",
      "error_message": null,
      "parameters": {
        "size": "medium",
        "material": "wood"
      },
      "created_at": "2026-05-11T10:30:00+00:00"
    }
  ]
}
```

### Error Responses

Prompt not found:

```http
404 Not Found
```

```json
{
  "error": "Prompt not found"
}
```

User not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this prompt"
}
```

---

## 2.3 Get Current User Prompt History

```http
GET /prompts/me
```

Returns all root prompts created by the authenticated user.

Modified versions are not returned as separate root items because prompts with `parent_prompt_id` are skipped.

### Authentication

Required.

### Success Response

Status code:

```http
200 OK
```

Response:

```json
{
  "user_id": 1,
  "username": "user",
  "prompts": [
    {
      "id": 1,
      "prompt": "Create a modern wooden chair",
      "status": "COMPLETED",
      "result_path": "static/models/result.glb",
      "error_message": null,
      "modification_command": null,
      "created_at": "2026-05-11T10:30:00+00:00"
    }
  ]
}
```

### Error Responses

User not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

User not found:

```http
404 Not Found
```

```json
{
  "error": "User not found"
}
```

---

## 2.4 Download Generated File

```http
GET /prompts/{id}/download
```

Downloads the generated file for a prompt as an attachment.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Prompt ID |

### Behavior

The backend:

1. Retrieves the prompt.
2. Checks authentication.
3. Checks ownership.
4. Checks that `result_path` exists.
5. Looks for the file in the `static/models` directory.
6. Returns the file as an attachment.

### Success Response

Returns the generated file as an attachment.

Example:

```txt
result.glb
```

### Error Responses

Prompt not found:

```http
404 Not Found
```

```json
{
  "error": "Prompt not found"
}
```

User not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this asset"
}
```

No generated file:

```http
404 Not Found
```

```json
{
  "error": "No generated file for this prompt"
}
```

File not found on server:

```http
404 Not Found
```

```json
{
  "error": "File not found on server: path/to/file"
}
```

---

## 2.5 Serve Generated File

```http
GET /prompts/{id}/file
```

Serves the generated file directly, usually for frontend preview.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Prompt ID |

### Success Response

Returns the generated file directly.

Unlike `/download`, this endpoint does not force the file to be downloaded as an attachment.

### Error Responses

Same as:

```http
GET /prompts/{id}/download
```

---

## 2.6 Modify Generated Prompt Result

```http
POST /prompts/{id}/modify
```

Creates a new prompt version based on an existing generated prompt.

This endpoint is used for iterative refinement.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Original prompt ID |

### Request Body

The request can contain a modification command:

```json
{
  "command": "Make the chair larger and change the material to metal"
}
```

It can also contain updated parameters:

```json
{
  "parameters": {
    "size": "large",
    "material": "metal"
  }
}
```

Or both:

```json
{
  "command": "Make it more modern",
  "parameters": {
    "style": "modern"
  }
}
```

### Behavior

The backend:

1. Checks if the user is authenticated.
2. Retrieves the original prompt.
3. Checks that the original prompt belongs to the user.
4. Reads `command` and/or `parameters`.
5. Validates incoming parameters if provided.
6. Creates a new `PromptRequest`.
7. Links the new prompt to the original one using `parent_prompt_id`.
8. Stores the modification command.
9. Starts a Celery task using `fast_track_id`.

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "id": 2,
  "status": "QUEUED",
  "message": "Modification started",
  "parent_id": 1,
  "created_at": "2026-05-11T10:40:00+00:00"
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Unauthorized:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized"
}
```

Missing command or parameters:

```http
400 Bad Request
```

```json
{
  "error": "Missing command or parameters"
}
```

Invalid parameters:

```http
400 Bad Request
```

```json
{
  "error": "Validation error message"
}
```

---

## 2.7 Submit Feedback

```http
POST /prompts/{id}/feedback
```

Submits feedback for a generated prompt result.

A user can submit only one feedback entry per prompt.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Prompt ID |

### Request Body

```json
{
  "rating": "positive",
  "accuracy_score": 5,
  "quality_score": 4,
  "comment": "The result matches the prompt and looks good."
}
```

### Accepted Rating Values

```txt
positive
neutral
negative
```

### Score Rules

Both `accuracy_score` and `quality_score` must be between:

```txt
1 and 5
```

They are optional, but if provided, they must respect this range.

### Behavior

The backend:

1. Checks authentication.
2. Retrieves the prompt.
3. Checks ownership.
4. Prevents duplicate feedback for the same prompt and user.
5. Validates the rating.
6. Validates the scores.
7. Stores feedback linked to:
   - prompt
   - user
   - LLM output
   - parameters
   - result path

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "id": 1,
  "prompt_id": 1,
  "user_id": 1,
  "rating": "positive",
  "accuracy_score": 5,
  "quality_score": 4,
  "comment": "The result matches the prompt and looks good."
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Prompt not found:

```http
404 Not Found
```

```json
{
  "error": "Prompt not found"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this prompt"
}
```

Duplicate feedback:

```http
409 Conflict
```

```json
{
  "error": "Feedback already submitted for this prompt"
}
```

Invalid rating:

```http
400 Bad Request
```

```json
{
  "error": "Invalid rating. Use positive, neutral or negative."
}
```

Invalid score:

```http
400 Bad Request
```

```json
{
  "error": "accuracy_score must be between 1 and 5"
}
```

or:

```json
{
  "error": "quality_score must be between 1 and 5"
}
```

---

## 2.8 Get Feedback Analytics

```http
GET /prompts/feedback/analytics
```

Returns aggregated feedback analytics.

### Authentication

Currently not enforced in the code because the authentication check is commented out.

### Behavior

The backend:

1. Retrieves all feedback entries.
2. Counts total feedback.
3. Calculates success rate.
4. Calculates average accuracy score.
5. Calculates average quality score.
6. Counts ratings.
7. Returns comments with prompt-related information.

A feedback is considered successful if at least one of the following is true:

- rating is `positive`
- accuracy score is greater than or equal to 4
- quality score is greater than or equal to 4

### Success Response

```json
{
  "total_feedback": 10,
  "success_rate": 80.0,
  "average_accuracy_score": 4.2,
  "average_quality_score": 4.5,
  "ratings": {
    "positive": 8,
    "neutral": 1,
    "negative": 1
  },
  "comments": [
    {
      "id": 1,
      "prompt_id": 1,
      "user_id": 1,
      "rating": "positive",
      "accuracy_score": 5,
      "quality_score": 4,
      "comment": "Good result",
      "prompt": "Create a chair",
      "modification_command": null,
      "modified_at": "2026-05-11T10:35:00+00:00",
      "created_at": "2026-05-11T10:36:00+00:00"
    }
  ]
}
```

### Empty Response

If there is no feedback:

```json
{
  "total_feedback": 0,
  "success_rate": 0,
  "average_accuracy_score": null,
  "average_quality_score": null,
  "ratings": {},
  "comments": []
}
```

---

## 2.9 Export Feedback CSV

```http
GET /prompts/feedback/export
```

Exports feedback data as a CSV file, mainly for Power BI or external analytics.

### Authentication

Currently not enforced in the code because the authentication check is commented out.

### Response

Returns a CSV file with the following filename:

```txt
powerbi_generation_feedback.csv
```

### CSV Columns

```csv
feedback_id,
prompt_id,
user_id,
rating,
accuracy_score,
quality_score,
success_label,
success_rate_value,
comment,
prompt_text,
modification_command,
parameters,
result_path,
is_modified_version,
parent_prompt_id,
created_at
```

### Notes

The column `success_rate_value` contains `1` for successful results and `0` for unsuccessful results.

This allows Power BI to calculate the success rate using an average aggregation.

---

# 3. Asset Endpoints

The asset endpoints are defined in `assets.py`.

Base prefix:

```http
/assets
```

These endpoints allow users to upload, list, inspect and modify imported 3D assets.

Allowed file formats are:

```txt
glb
gltf
obj
```

---

## 3.1 Import Asset

```http
POST /assets/import
```

Uploads an existing 3D asset.

### Authentication

Required.

### Request Type

```txt
multipart/form-data
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | The 3D asset file to upload |

### Supported Formats

```txt
.glb
.gltf
.obj
```

### Behavior

The backend:

1. Checks authentication.
2. Checks that a file was provided.
3. Checks that a filename exists.
4. Validates the file extension.
5. Secures the filename.
6. Generates a unique filename using UUID.
7. Saves the file in:

```txt
static/models/imported
```

8. Extracts metadata using `AssetMetadataService`.
9. Creates an `ImportedAsset` database entry.
10. Returns the asset information.

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "id": 1,
  "filename": "uuid_chair.glb",
  "original_filename": "chair.glb",
  "file_type": "glb",
  "file_path": "static/models/imported/uuid_chair.glb",
  "user_id": 1,
  "message": "Asset imported successfully"
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

No file provided:

```http
400 Bad Request
```

```json
{
  "error": "No file provided"
}
```

No selected file:

```http
400 Bad Request
```

```json
{
  "error": "No selected file"
}
```

Unsupported format:

```http
400 Bad Request
```

```json
{
  "error": "Unsupported file format. Allowed formats: glb, gltf, obj"
}
```

---

## 3.2 Get Imported Asset by ID

```http
GET /assets/{id}
```

Returns details about one imported asset.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Imported asset ID |

### Behavior

The backend:

1. Checks authentication.
2. Retrieves the imported asset.
3. Checks that the asset belongs to the current user.
4. Returns asset details and metadata.

### Success Response

```json
{
  "id": 1,
  "filename": "uuid_chair.glb",
  "original_filename": "chair.glb",
  "file_type": "glb",
  "file_path": "static/models/imported/uuid_chair.glb",
  "user_id": 1,
  "metadata": {
    "extension": ".glb"
  },
  "uploaded_at": "2026-05-11T10:30:00"
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Asset not found:

```http
404 Not Found
```

```json
{
  "error": "Imported asset not found"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this asset"
}
```

---

## 3.3 Get Current User Imported Assets

```http
GET /assets/me
```

Returns all imported assets belonging to the authenticated user.

### Authentication

Required.

### Behavior

The backend:

1. Checks authentication.
2. Finds all imported assets linked to the current user.
3. Orders them by upload date in descending order.
4. Returns the list of assets.

### Success Response

```json
{
  "user_id": 1,
  "assets": [
    {
      "id": 1,
      "filename": "uuid_chair.glb",
      "original_filename": "chair.glb",
      "file_type": "glb",
      "file_path": "static/models/imported/uuid_chair.glb",
      "metadata": {
        "extension": ".glb"
      },
      "uploaded_at": "2026-05-11T10:30:00"
    }
  ]
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

---

## 3.4 Get Imported Asset Metadata

```http
GET /assets/{id}/metadata
```

Returns only the metadata of an imported asset.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Imported asset ID |

### Behavior

The backend:

1. Checks authentication.
2. Retrieves the imported asset.
3. Checks ownership.
4. Returns the metadata only.

### Success Response

```json
{
  "id": 1,
  "original_filename": "chair.glb",
  "file_type": "glb",
  "metadata": {
    "extension": ".glb"
  }
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Asset not found:

```http
404 Not Found
```

```json
{
  "error": "Imported asset not found"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this asset"
}
```

---

## 3.5 Modify Imported Asset

```http
POST /assets/{id}/modify
```

Creates a prompt request to modify an imported 3D asset.

### Authentication

Required.

### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `id` | integer | Imported asset ID |

### Request Body

```json
{
  "command": "Make the object bigger and change its color to blue"
}
```

### Behavior

The backend:

1. Checks authentication.
2. Retrieves the imported asset.
3. Checks ownership.
4. Reads the modification command.
5. Creates a new `PromptRequest`.
6. Links the prompt to the imported asset using `imported_asset_id`.
7. Sets the prompt status to `QUEUED`.
8. Starts the Celery task with the imported asset ID.

### Success Response

Status code:

```http
201 Created
```

Response:

```json
{
  "id": 2,
  "status": "QUEUED",
  "message": "Imported asset modification task started",
  "imported_asset_id": 1,
  "asset_path": "static/models/imported/uuid_chair.glb",
  "metadata": {
    "extension": ".glb"
  },
  "command": "Make the object bigger and change its color to blue"
}
```

### Error Responses

Not authenticated:

```http
401 Unauthorized
```

```json
{
  "error": "Not authenticated"
}
```

Asset not found:

```http
404 Not Found
```

```json
{
  "error": "Imported asset not found"
}
```

Unauthorized access:

```http
403 Forbidden
```

```json
{
  "error": "Unauthorized access to this asset"
}
```

Missing modification command:

```http
400 Bad Request
```

```json
{
  "error": "Missing modification command"
}
```

---

# 4. Endpoint Summary

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/` | Check if API is running | No |
| POST | `/auth/signup` | Create a new user account | No |
| POST | `/auth/login` | Log in a user | No |
| GET | `/auth/me` | Get current authenticated user | Yes |
| POST | `/auth/logout` | Log out current user | No |
| POST | `/prompts` | Create a generation prompt | Yes |
| GET | `/prompts/{id}` | Get prompt details and version history | Yes |
| GET | `/prompts/me` | Get current user's prompt history | Yes |
| GET | `/prompts/{id}/download` | Download generated file | Yes |
| GET | `/prompts/{id}/file` | Serve generated file for preview | Yes |
| POST | `/prompts/{id}/modify` | Modify a generated prompt result | Yes |
| POST | `/prompts/{id}/feedback` | Submit feedback for a prompt | Yes |
| GET | `/prompts/feedback/analytics` | Get feedback analytics | No, currently commented out |
| GET | `/prompts/feedback/export` | Export feedback as CSV | No, currently commented out |
| POST | `/assets/import` | Import a 3D asset | Yes |
| GET | `/assets/{id}` | Get imported asset details | Yes |
| GET | `/assets/me` | Get current user's imported assets | Yes |
| GET | `/assets/{id}/metadata` | Get imported asset metadata | Yes |
| POST | `/assets/{id}/modify` | Modify an imported asset | Yes |

---

# 5. Common Status Codes

| Status Code | Meaning |
|---|---|
| `200 OK` | Request completed successfully |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Invalid or missing request data |
| `401 Unauthorized` | User is not authenticated |
| `403 Forbidden` | User does not have access to this resource |
| `404 Not Found` | Resource not found |
| `409 Conflict` | Resource already exists or duplicate action |
| `500 Internal Server Error` | Unexpected server error |

---

# 6. Frontend Integration Workflow

## 6.1 Standard Generation Flow

1. User logs in using:

```http
POST /auth/login
```

2. Frontend submits a prompt:

```http
POST /prompts
```

3. Backend creates a `PromptRequest` with status `QUEUED`.

4. Backend starts the Celery generation task.

5. Frontend polls:

```http
GET /prompts/{id}
```

6. When status becomes `COMPLETED`, frontend displays the file using:

```http
GET /prompts/{id}/file
```

7. User can download the result using:

```http
GET /prompts/{id}/download
```

8. User can submit feedback using:

```http
POST /prompts/{id}/feedback
```

---

## 6.2 Prompt Modification Flow

1. User selects an existing generated result.
2. Frontend sends a modification request:

```http
POST /prompts/{id}/modify
```

3. Backend creates a new prompt linked to the original prompt through `parent_prompt_id`.
4. Celery processes the modification.
5. Frontend polls the new prompt ID:

```http
GET /prompts/{new_prompt_id}
```

6. Version history can be retrieved from:

```http
GET /prompts/{id}
```

---

## 6.3 Imported Asset Flow

1. User uploads an asset:

```http
POST /assets/import
```

2. Backend stores the file and extracts metadata.
3. Frontend can retrieve all imported assets:

```http
GET /assets/me
```

4. User can inspect metadata:

```http
GET /assets/{id}/metadata
```

5. User modifies the imported asset:

```http
POST /assets/{id}/modify
```

6. Backend creates a new prompt linked to the imported asset.
7. Celery processes the modification.
8. Frontend polls the generated prompt result:

```http
GET /prompts/{id}
```

---

# 7. Notes and Known Implementation Details

- Generated files are served from the `static/models` directory.
- Imported assets are stored in `static/models/imported`.
- Prompt modifications are stored as new `PromptRequest` entries.
- Prompt versioning uses `parent_prompt_id`.
- Imported asset modifications use `imported_asset_id`.
- Feedback is linked to both the prompt and the user.
- Analytics and CSV export currently use all feedback entries, not only the current user's feedback.
- Authentication checks for analytics and export exist in the code but are currently commented out.
- CORS allows requests from:
  - `http://127.0.0.1:3000`
  - `http://localhost:3000`

---

# 8. Suggested Manual Tests

## 8.1 Test Signup

```bash
curl -X POST http://localhost:5000/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"user@example.com\",\"password\":\"password123\"}" \
  -c cookies.txt
```

## 8.2 Test Login

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"user@example.com\",\"password\":\"password123\"}" \
  -c cookies.txt
```

## 8.3 Test Current User

```bash
curl -X GET http://localhost:5000/auth/me \
  -b cookies.txt
```

## 8.4 Test Prompt Creation

```bash
curl -X POST http://localhost:5000/prompts \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Create a modern wooden chair\"}" \
  -b cookies.txt
```

## 8.5 Test Prompt Status

```bash
curl -X GET http://localhost:5000/prompts/1 \
  -b cookies.txt
```

## 8.6 Test Prompt Modification

```bash
curl -X POST http://localhost:5000/prompts/1/modify \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"Make it bigger and change the material to metal\"}" \
  -b cookies.txt
```

## 8.7 Test Asset Import

```bash
curl -X POST http://localhost:5000/assets/import \
  -F "file=@chair.glb" \
  -b cookies.txt
```

## 8.8 Test Imported Assets List

```bash
curl -X GET http://localhost:5000/assets/me \
  -b cookies.txt
```

## 8.9 Test Imported Asset Modification

```bash
curl -X POST http://localhost:5000/assets/1/modify \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"Make this asset blue and larger\"}" \
  -b cookies.txt
```

## 8.10 Test Feedback Submission

```bash
curl -X POST http://localhost:5000/prompts/1/feedback \
  -H "Content-Type: application/json" \
  -d "{\"rating\":\"positive\",\"accuracy_score\":5,\"quality_score\":4,\"comment\":\"Good result\"}" \
  -b cookies.txt
```

## 8.11 Test Feedback Analytics

```bash
curl -X GET http://localhost:5000/prompts/feedback/analytics
```

## 8.12 Test Feedback CSV Export

```bash
curl -X GET http://localhost:5000/prompts/feedback/export \
  -o powerbi_generation_feedback.csv
```