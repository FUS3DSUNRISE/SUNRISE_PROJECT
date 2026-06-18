# Backend Architecture Documentation

## Overview

This document describes the backend architecture of the SUNRISE 3D asset generation system.

The backend is responsible for:

- exposing REST API endpoints
- managing user authentication
- storing users, prompts, imported assets and feedback
- validating generation parameters
- sending long-running generation jobs to Celery
- calling the LLM provider
- generating Blender Python scripts
- executing Blender in background mode
- exporting generated 3D models as GLB files
- serving generated files to the frontend
- collecting feedback and analytics data

The backend follows a modular layered architecture with clear separation between routes, models, services, asynchronous tasks and configuration.

---

# 1. Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Web framework | Flask | Exposes REST API endpoints |
| Database ORM | SQLAlchemy | Defines and manages database models |
| Migrations | Flask-Migrate / Alembic | Handles database schema migrations |
| Authentication | Flask sessions | Stores authenticated user ID in session |
| Async processing | Celery | Runs long generation tasks in the background |
| Message broker | Redis | Queues Celery tasks |
| LLM integration | LangChain `ChatOpenAI` | Calls the configured LLM provider |
| LLM provider | Groq-compatible OpenAI API | Generates Blender Python code |
| 3D engine | Blender | Executes Python scripts and exports 3D models |
| Asset formats | GLB / GLTF / OBJ | Generated or imported 3D asset formats |
| Configuration | python-dotenv | Loads environment variables |
| Testing | unittest / pytest / requests | Tests workflows and backend behavior |

---

# 2. Project Structure

The backend is organized around the following structure:

```txt
SUNRISE_PROJECT/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── celery_app.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── prompts.py
│   │   └── assets.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── prompt.py
│   │   ├── imported_asset.py
│   │   └── feedback.py
│   │
│   ├── tasks/
│   │   └── prompt_tasks.py
│   │
│   ├── services/
│   │   ├── prompt_service.py
│   │   ├── asset_metadata_service.py
│   │   ├── prompt_benchmark.py
│   │   │
│   │   ├── llm/
│   │   │   ├── base_provider.py
│   │   │   ├── groq_provider.py
│   │   │   └── llm_service.py
│   │   │
│   │   └── blender/
│   │       └── blender_executor.py
│   │
│   └── prompts/
│       └── system_prompt.txt
│
├── migrations/
├── tests/
├── static/
│   └── models/
│
├── config.py
├── run.py
├── worker.py
├── requirements.txt
└── README.md
```

---

# 3. Application Factory

The Flask application is created using the application factory pattern.

The main factory function is located in `app/__init__.py`.

```python
def create_app():
    app = Flask(__name__)
```

The application factory is responsible for:

- creating the Flask application
- loading configuration from `config.py`
- initializing extensions
- configuring CORS
- registering route blueprints
- exposing the root health endpoint

The backend registers three main blueprints:

```python
app.register_blueprint(prompts_bp, url_prefix="/prompts")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(assets_bp, url_prefix="/assets")
```

This means the backend exposes routes under:

```txt
/auth
/prompts
/assets
```

The root endpoint is:

```http
GET /
```

It returns:

```txt
API is running
```

---

# 4. Extensions

The backend uses centralized Flask extensions defined in `app/extensions.py`.

```python
db = SQLAlchemy()
migrate = Migrate()
```

These extensions are initialized in the Flask application factory.

```python
db.init_app(app)
migrate.init_app(app, db)
```

## SQLAlchemy

SQLAlchemy is used to define the database models and interact with the database.

## Flask-Migrate / Alembic

Flask-Migrate and Alembic are used to manage database schema migrations.

The migration environment is configured to use the Flask application database engine and metadata.

---

# 5. Configuration Layer

Configuration is defined in `config.py`.

The configuration includes:

- debug mode
- secret key
- database URI
- SQLAlchemy settings
- Celery broker URL
- Celery result backend
- LLM provider settings
- session cookie settings
- Power BI export token
- system prompt path

Example database configuration:

```python
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///app.db"
)
```

This means the backend can use:

- SQLite by default for local development
- PostgreSQL when `DATABASE_URL` is provided

Redis is configured as both the Celery broker and result backend:

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

LLM configuration:

```python
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
```

The system prompt path is configurable:

```python
LLM_SYSTEM_PROMPT_PATH = os.getenv(
    "LLM_SYSTEM_PROMPT_PATH",
    os.path.join(BASE_DIR, "app", "prompts", "system_prompt.txt")
)
```

---

# 6. CORS Configuration

The backend allows requests from the local frontend development servers:

```txt
http://127.0.0.1:3000
http://localhost:3000
```

CORS is configured with credentials enabled.

This is required because the backend uses session-based authentication with cookies.

---

# 7. Route Layer

The route layer receives HTTP requests, validates input, checks authentication and calls the appropriate services or background tasks.

The backend currently has three main route modules:

```txt
routes/auth.py
routes/prompts.py
routes/assets.py
```

---

## 7.1 Authentication Routes

Authentication routes are registered under:

```txt
/auth
```

Main endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/signup` | Create a new user account |
| `POST` | `/auth/login` | Log in an existing user |
| `GET` | `/auth/me` | Get the current authenticated user |
| `POST` | `/auth/logout` | Log out the current user |

Authentication is session-based.

After signup or login, the backend stores the authenticated user ID in the Flask session:

```python
session["user_id"] = user.id
```

Protected routes check whether `user_id` exists in the session.

---

## 7.2 Prompt Routes

Prompt routes are registered under:

```txt
/prompts
```

Main endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/prompts` | Create a new generation prompt |
| `GET` | `/prompts/{id}` | Get prompt details and version history |
| `GET` | `/prompts/me` | Get current user's prompt history |
| `GET` | `/prompts/{id}/download` | Download generated file |
| `GET` | `/prompts/{id}/file` | Serve generated file |
| `POST` | `/prompts/{id}/modify` | Modify a generated result |
| `POST` | `/prompts/{id}/feedback` | Submit feedback |
| `GET` | `/prompts/feedback/analytics` | Get feedback analytics |
| `GET` | `/prompts/feedback/export` | Export feedback CSV |

The prompt route is also responsible for starting Celery tasks.

Example:

```python
process_prompt_task.delay(
    prompt_id=prompt.id,
    parameters=data.get("parameters", {})
)
```

---

## 7.3 Asset Routes

Asset routes are registered under:

```txt
/assets
```

Main endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/assets/import` | Upload an existing 3D asset |
| `GET` | `/assets/{id}` | Get imported asset details |
| `GET` | `/assets/me` | Get current user's imported assets |
| `GET` | `/assets/{id}/metadata` | Get imported asset metadata |
| `POST` | `/assets/{id}/modify` | Modify an imported asset |

Supported imported file formats:

```txt
.glb
.gltf
.obj
```

Imported files are stored in:

```txt
static/models/imported
```

---

# 8. Model Layer

The model layer defines the database schema using SQLAlchemy.

The current backend models are:

```txt
User
PromptRequest
ImportedAsset
GenerationFeedback
```

## 8.1 User

The `User` model stores application users.

Main fields:

```txt
id
username
email
password_hash
```

Relationships:

```txt
User 1 ──── * PromptRequest
User 1 ──── * ImportedAsset
User 1 ──── * GenerationFeedback
```

The user model is used for:

- signup
- login
- session-based authentication
- prompt ownership
- imported asset ownership
- feedback ownership

---

## 8.2 PromptRequest

The `PromptRequest` model is the central model of the backend.

It stores:

```txt
id
prompt_text
parameters
generated_code
modification_command
status
created_at
updated_at
result_path
error_message
user_id
parent_prompt_id
imported_asset_id
```

Prompt statuses include:

```txt
queued
processing
completed
failed
ambiguous
awaiting_clarification
invalid
```

The model supports prompt versioning through:

```txt
parent_prompt_id
```

This allows the backend to represent modifications and refinements as new prompt versions.

The model also supports imported asset modification through:

```txt
imported_asset_id
```

This links a prompt request to an uploaded asset.

---

## 8.3 ImportedAsset

The `ImportedAsset` model stores uploaded 3D files.

It stores:

```txt
id
filename
original_filename
file_path
file_type
uploaded_at
user_id
metadata_json
```

The model is used for:

- storing imported files
- linking imported files to users
- storing extracted metadata
- allowing imported assets to be modified through the prompt pipeline

---

## 8.4 GenerationFeedback

The `GenerationFeedback` model stores user feedback on generated assets.

It stores:

```txt
id
prompt_id
user_id
rating
accuracy_score
quality_score
comment
llm_output
parameters
result_path
created_at
```

Feedback ratings include:

```txt
positive
neutral
negative
```

The model is used for:

- collecting user feedback
- evaluating generation quality
- calculating analytics
- exporting data to CSV for Power BI

---

# 9. Service Layer

The service layer contains reusable business logic separated from route handlers.

Main services:

```txt
PromptService
AssetMetadataService
LLMService
GroqProvider
Blender Executor
Prompt Benchmark
```

---

## 9.1 PromptService

`PromptService` handles prompt-related logic.

It includes:

- Pydantic parameter schemas
- prompt construction for the LLM
- prompt classification
- final prompt generation

Expected parameter structure:

```json
{
  "size": {
    "width": 1.5,
    "height": 2.0,
    "depth": 1.2
  },
  "geometry": {
    "complexity": 5,
    "smoothness": 50
  },
  "material": {
    "material_type": "Wood",
    "roughness": 0.5,
    "metallic": 0.0
  }
}
```

Parameter constraints:

| Parameter | Range / Values |
|---|---|
| `width` | `0.5` to `5` |
| `height` | `0.5` to `5` |
| `depth` | `0.5` to `5` |
| `complexity` | `1` to `10` |
| `smoothness` | `1` to `100` |
| `material_type` | `Plastic`, `Metal`, `Wood`, `Glass` |
| `roughness` | `0.0` to `1.0` |
| `metallic` | `0.0` to `1.0` |

Prompt classification returns one of:

```txt
proceed
clarify
block
```

---

## 9.2 AssetMetadataService

`AssetMetadataService` extracts metadata from uploaded 3D files.

Supported formats:

| Format | Extraction method |
|---|---|
| `.obj` | Reads object/group names, vertex count and face count |
| `.gltf` | Reads JSON structure |
| `.glb` | Reads binary GLB header and JSON chunk |

Extracted metadata can include:

```json
{
  "original_filename": "chair.glb",
  "extension": ".glb",
  "file_size_bytes": 123456,
  "interpretable": true,
  "objects": [],
  "meshes": [],
  "materials": [],
  "object_count": 0,
  "mesh_count": 0,
  "material_count": 0
}
```

If metadata extraction fails, the asset is marked as not interpretable:

```json
{
  "interpretable": false,
  "error": "Error message"
}
```

---

## 9.3 LLMService

`LLMService` acts as an abstraction layer over LLM providers.

It reads the configured provider from:

```txt
LLM_PROVIDER
```

Currently supported provider:

```txt
groq
```

If the provider is `groq`, `LLMService` instantiates `GroqProvider`.

This structure makes it easier to add additional LLM providers later.

Possible future providers:

```txt
OpenAI
Anthropic
Mistral
Local model
```

---

## 9.4 GroqProvider

`GroqProvider` wraps the LangChain `ChatOpenAI` client.

It uses:

```txt
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
LLM_TEMPERATURE
LLM_TOP_P
LLM_MAX_TOKENS
```

The provider sends two messages to the LLM:

```python
[
    ("system", system_prompt),
    ("human", human_prompt)
]
```

It returns the raw LLM response content.

---

## 9.5 Blender Executor

The Blender executor is responsible for safely running generated Blender Python code.

It provides:

```txt
write_script()
cleanup_file()
run_blender_script()
get_blender_executable()
```

Main responsibilities:

- write generated code to a temporary script
- check script size
- restrict file permissions
- find Blender executable
- run Blender in background mode
- enforce execution timeout
- validate output extension
- check output file existence
- clean up temporary scripts

The script size is limited to:

```txt
512 KB
```

The Blender timeout is capped at:

```txt
120 seconds
```

Allowed output extensions:

```txt
.glb
.gltf
.blend
.png
.obj
.fbx
```

---

## 9.6 Prompt Benchmark

The benchmark service evaluates generated 3D assets using predefined test prompts and scoring metrics.

Benchmark categories include:

```txt
compliance
stability
geometry_quality
materials
blender_success
final_export
```

Prompts are grouped by difficulty:

```txt
Simple
Medium
Difficult
Ambiguous
```

This module helps compare generation quality and track progress over different LLM configurations or prompt versions.

---

# 10. LLM to Blender Pipeline

The core backend pipeline is:

```txt
User prompt
   |
   v
Prompt validation
   |
   v
PromptRequest created
   |
   v
Celery task queued
   |
   v
LLM prompt built
   |
   v
System prompt + human prompt sent to LLM
   |
   v
Blender Python code returned
   |
   v
Generated code validated
   |
   v
Temporary Python script written
   |
   v
Blender runs script in background mode
   |
   v
GLB file exported
   |
   v
PromptRequest updated with result path
```

---

# 11. System Prompt

The system prompt instructs the LLM to behave as a Blender Python script generator.

Important rules:

- output only raw executable Python code
- start with `import bpy, math, bmesh`
- do not output Markdown
- use Blender Python
- include helper functions for primitive objects
- export the final result as GLB

The system prompt includes helper functions such as:

```txt
make_box
make_cylinder
make_sphere
set_material
build_chair
build_table
build_tree
```

These helper functions guide the LLM toward producing valid and consistent Blender scripts.

---

# 12. Asynchronous Task Layer

Long-running generation is handled by Celery.

The main task is:

```txt
process_prompt_task
```

The task supports three generation modes:

| Mode | Description |
|---|---|
| `creation` | Generates a new 3D asset from a user prompt |
| `fast_track_modification` | Modifies a previously generated prompt using existing code |
| `imported_asset_modification` | Modifies an uploaded asset file |

The task lifecycle is generally:

```txt
queued
processing
completed
```

or:

```txt
queued
processing
failed
```

The task updates the database at each important step.

---

## 12.1 Creation Mode

Creation mode is used when the user submits a new prompt.

Triggered by:

```http
POST /prompts
```

The task builds a generation prompt and asks the LLM to create Blender Python code from scratch.

---

## 12.2 Fast-Track Modification Mode

Fast-track modification is used when the user modifies a previously generated prompt.

Triggered by:

```http
POST /prompts/{id}/modify
```

The backend creates a new `PromptRequest` and links it to the original prompt using:

```txt
parent_prompt_id
```

The Celery task receives:

```txt
fast_track_id
```

The task then asks the LLM to revise the existing generated Blender script.

---

## 12.3 Imported Asset Modification Mode

Imported asset modification is used when the user modifies an uploaded 3D asset.

Triggered by:

```http
POST /assets/{id}/modify
```

The backend creates a new `PromptRequest` linked to the imported asset using:

```txt
imported_asset_id
```

The task receives:

```txt
imported_asset_id
```

The LLM is instructed to:

- import the existing file
- preserve the asset structure
- modify existing mesh objects
- avoid modifying non-mesh objects
- export the final result as GLB

---

# 13. Celery and Redis Architecture

Celery is configured using the Flask app configuration.

The Celery app is created in `app/celery_app.py`.

```python
def make_celery(app):
    celery = Celery(app.import_name)

    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
```

The worker is defined in `worker.py`.

```python
from app import create_app
from app.celery_app import make_celery

app = create_app()
celery = make_celery(app)

import app.tasks.prompt_tasks
```

Redis acts as:

- Celery message broker
- Celery result backend

The worker should be started with:

```bash
celery -A worker.celery worker --loglevel=info --pool=solo
```

---

# 14. File Storage Architecture

The backend stores generated and imported assets in the `static/models` directory.

## Generated Files

Generated GLB files are stored as:

```txt
static/models/prompt_<prompt_id>.glb
```

Example:

```txt
static/models/prompt_12.glb
```

The database stores the result path in:

```txt
PromptRequest.result_path
```

Example:

```txt
/static/models/prompt_12.glb
```

## Imported Files

Imported files are stored in:

```txt
static/models/imported
```

The stored filename includes a UUID prefix to avoid collisions.

Example:

```txt
static/models/imported/ceb97b1e380b492587b48c2a84c9c360_chair.glb
```

The database stores this path in:

```txt
ImportedAsset.file_path
```

---

# 15. Authentication and Authorization

Authentication is session-based.

The session stores:

```python
session["user_id"] = user.id
```

Protected endpoints check that the user is authenticated before proceeding.

Authorization is handled by checking resource ownership.

Examples:

- a user can only access their own prompts
- a user can only download their own generated assets
- a user can only access their own imported assets
- a user can only modify their own imported assets
- a user can only submit feedback for their own prompt

If the resource does not belong to the current user, the backend returns a `403 Forbidden` response.

---

# 16. Feedback and Analytics Architecture

Feedback is submitted through:

```http
POST /prompts/{id}/feedback
```

The backend stores:

- rating
- accuracy score
- quality score
- comment
- generated LLM output
- parameters
- result path

Analytics are exposed through:

```http
GET /prompts/feedback/analytics
```

CSV export is exposed through:

```http
GET /prompts/feedback/export
```

The analytics endpoint calculates:

- total feedback count
- success rate
- average accuracy score
- average quality score
- rating breakdown
- comments

A feedback entry is considered successful if at least one of the following is true:

```txt
rating == positive
accuracy_score >= 4
quality_score >= 4
```

---

# 17. Testing Architecture

The backend includes several test files for validating routes, workflows and services.

Current test files include:

```txt
test_feedback.py
test_import_asset.py
test_modify_workflow.py
test_prompt_benchmark.py
test_prompt_tasks.py
test_prompts.py
```

## 17.1 Feedback Tests

The feedback test workflow checks:

- signup or login
- feedback submission
- analytics endpoint
- CSV export endpoint

## 17.2 Imported Asset Tests

The imported asset workflow checks:

- login
- valid GLB upload
- metadata extraction
- asset retrieval by ID
- asset listing through `/assets/me`
- imported asset modification
- polling until prompt completion
- generated GLB file access
- invalid file rejection

## 17.3 Modification Workflow Tests

The modification workflow checks:

- base prompt creation
- polling prompt status
- modification with parameters only
- modification with command only
- modification with command and parameters
- multi-step version history
- branching from previous prompt versions

## 17.4 Prompt Benchmark Tests

Benchmark tests check:

- benchmark difficulty categories
- scoring calculation
- average score by test
- average score by difficulty
- overall average
- table-friendly report rows
- desktop benchmark viewer generation
- invalid score handling

## 17.5 Celery Task Tests

Prompt task tests check:

- parameterized prompt usage
- generated code persistence
- result path generation
- fast-track modification using saved code
- removal of hardcoded Blender path

## 17.6 Prompt Route Tests

Prompt route tests check:

- authenticated prompt creation
- successful prompt creation response
- task queuing behavior

---

# 18. Error Handling Strategy

The backend handles errors at different levels.

## 18.1 Route-Level Errors

Examples:

- missing JSON body
- missing prompt
- invalid parameters
- unauthenticated user
- unauthorized access
- missing file
- unsupported file format
- duplicate feedback

Common status codes:

```txt
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
```

---

## 18.2 Task-Level Errors

The Celery task handles:

- configuration errors
- LLM errors
- Blender execution errors
- unexpected exceptions

When a task-level error occurs, the related prompt is updated with:

```txt
status = failed
error_message = error details
```

The frontend can retrieve this error through:

```http
GET /prompts/{id}
```

---

# 19. Logging

The backend uses logging mainly inside:

```txt
app/tasks/prompt_tasks.py
app/services/blender/blender_executor.py
```

The task logs:

- prompt loading
- task start
- LLM configuration
- generation mode
- LLM prompt preview
- LLM response time
- generated code validation
- temporary script creation
- Blender execution
- task completion
- errors and retries

This helps debug failed generations and trace the full pipeline.

---

# 20. Security and Safety Considerations

The backend includes several safety mechanisms.

## Authentication

Most user-specific endpoints require an authenticated session.

## Authorization

Prompt and asset access is restricted by user ownership.

## File Validation

Imported assets are restricted to:

```txt
glb
gltf
obj
```

## Blender Execution Safety

The Blender executor:

- uses a controlled temporary script directory
- restricts temporary script permissions
- limits script size
- validates output extensions
- caps execution timeout
- checks for Blender executable validity
- removes temporary scripts after execution

## LLM Output Validation

The generated code must contain:

```python
import bpy
```

If this check fails, the prompt is marked as failed.

## Secrets

Sensitive values should be stored in `.env` and not committed.

Examples:

```txt
SECRET_KEY
DATABASE_URL
LLM_API_KEY
```

---

# 21. Backend Execution Flow Summary

## New Generation

```txt
POST /prompts
   |
   v
Validate user + prompt + parameters
   |
   v
Classify prompt intent
   |
   v
Create PromptRequest(status=queued)
   |
   v
Queue process_prompt_task(prompt_id)
   |
   v
Celery updates status=processing
   |
   v
Build LLM prompt
   |
   v
Call LLM provider
   |
   v
Validate generated code
   |
   v
Write temporary script
   |
   v
Run Blender
   |
   v
Export GLB
   |
   v
Update PromptRequest(status=completed, result_path=...)
```

---

## Prompt Modification

```txt
POST /prompts/{id}/modify
   |
   v
Validate user ownership
   |
   v
Create new PromptRequest(parent_prompt_id=original.id)
   |
   v
Queue process_prompt_task(fast_track_id=original.id)
   |
   v
LLM revises existing Blender script
   |
   v
Blender exports new GLB
   |
   v
Update new PromptRequest
```

---

## Imported Asset Modification

```txt
POST /assets/import
   |
   v
Store uploaded file
   |
   v
Extract metadata
   |
   v
Create ImportedAsset
   |
   v
POST /assets/{id}/modify
   |
   v
Create PromptRequest(imported_asset_id=asset.id)
   |
   v
Queue process_prompt_task(imported_asset_id=asset.id)
   |
   v
LLM generates code to import and modify existing asset
   |
   v
Blender exports modified GLB
   |
   v
Update PromptRequest
```

---

# 22. Current Limitations

The current backend architecture has a few known limitations:

- Only the Groq provider is currently implemented.
- Analytics and CSV export currently use all feedback entries.
- Authentication checks for analytics/export are currently commented out.
- Generated code validation currently checks mainly for `import bpy`.
- The backend depends on Blender being installed and correctly configured.
- Redis and Celery must be running separately for generation tasks to process.
- The frontend and backend must share cookies correctly for session-based authentication.

---

# 23. Future Improvements

Possible future backend improvements include:

- add a `Scene` model and scene composition endpoints
- add support for multiple LLM providers
- strengthen generated code validation
- add role-based access control
- protect analytics and export endpoints
- store generation metrics such as execution time and token usage
- improve retry behavior for Blender errors
- add Docker Compose for backend, Redis and database
- add automated benchmark execution for standard prompts
- add more advanced asset metadata extraction
- add automated integration tests for the full LLM-to-Blender pipeline
- add deployment configuration for shared demo usage

---

# 24. Summary

The backend architecture is organized around clear responsibilities.

| Layer | Responsibility |
|---|---|
| Routes | Receive HTTP requests and return API responses |
| Models | Store users, prompts, assets and feedback |
| Services | Handle prompt preparation, metadata extraction, LLM calls and Blender execution |
| Tasks | Run long generation workflows asynchronously |
| Redis | Queue background jobs |
| Celery | Execute background jobs |
| Blender | Generate and export 3D assets |
| Database | Store state, outputs, ownership and errors |
| Tests | Validate workflows, services and backend behavior |

This structure keeps the HTTP API responsive while allowing the system to perform heavy 3D generation tasks in the background.