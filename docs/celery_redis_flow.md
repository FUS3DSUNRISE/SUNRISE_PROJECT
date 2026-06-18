# Celery and Redis Async Flow Documentation

## Overview

This document explains how the backend handles asynchronous 3D generation tasks using Celery and Redis.

The system uses Celery because 3D generation is a long-running process. A single generation request can involve:

- validating the prompt and parameters
- preparing the LLM input
- calling the LLM provider
- receiving Blender Python code
- writing a temporary Python script
- executing Blender in background mode
- exporting a GLB file
- updating the database with the final result or error

Instead of making the user wait inside the HTTP request, the backend creates a database record, queues a Celery task, and lets a background worker process the generation.

---

## Main Components

| Component | Role |
|---|---|
| Flask API | Receives requests from the frontend |
| SQLAlchemy Database | Stores prompts, statuses, generated code, result paths and errors |
| Redis | Message broker and result backend for Celery |
| Celery | Executes generation tasks in the background |
| LLMService | Chooses the configured LLM provider |
| GroqProvider | Sends prompts to the Groq-compatible OpenAI API |
| PromptService | Builds generation prompts and validates parameters |
| Blender Executor | Writes scripts, launches Blender and checks exported files |
| Frontend | Submits prompts and polls the API for status updates |

---

## Configuration

Redis is configured in `config.py`.

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

The broker URL tells Celery where to send queued tasks.

The result backend tells Celery where task results can be stored.

The application also loads the LLM configuration from `config.py`:

```python
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
```

The system prompt path is also configurable:

```python
LLM_SYSTEM_PROMPT_PATH = os.getenv(
    "LLM_SYSTEM_PROMPT_PATH",
    os.path.join(BASE_DIR, "app", "prompts", "system_prompt.txt")
)
```

---

## Celery Application Setup

Celery is initialized in `app/celery_app.py`.

```python
from celery import Celery


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

The custom `ContextTask` ensures that Celery tasks run inside the Flask application context.

This is important because the task needs access to:

- Flask configuration
- SQLAlchemy database session
- application paths
- models and services

---

## Worker Setup

The Celery worker is defined in `worker.py`.

```python
from app import create_app
from app.celery_app import make_celery

app = create_app()
celery = make_celery(app)

import app.tasks.prompt_tasks
```

The worker creates the Flask app, creates a Celery instance using the Flask configuration, and imports the task module so that Celery can register the available tasks.

The main registered task is:

```txt
app.tasks.prompt_tasks.process_prompt_task
```

---

## Running the System Locally

### 1. Start Redis

Using local Redis:

```bash
redis-server
```

Or using Docker:

```bash
docker run -p 6379:6379 redis
```

### 2. Start the Flask backend

```bash
python run.py
```

or:

```bash
flask run
```

### 3. Start the Celery worker

```bash
celery -A worker.celery worker --loglevel=info
```

Expected task registration should include:

```txt
app.tasks.prompt_tasks.process_prompt_task
```

---

# 1. High-Level Async Flow

```txt
Frontend
   |
   | POST /prompts
   v
Flask API
   |
   | Create PromptRequest
   | status = queued
   |
   | process_prompt_task.delay(...)
   v
Redis
   |
   | Stores queued task
   v
Celery Worker
   |
   | Reads task from Redis
   | Loads PromptRequest
   | status = processing
   | Builds LLM prompt
   | Calls LLM
   | Writes Blender script
   | Runs Blender
   | Exports GLB
   | status = completed or failed
   v
Database
   |
   | Frontend polls GET /prompts/{id}
   v
Frontend
```

---

# 2. Standard Prompt Generation Flow

## Step 1 — Frontend submits a prompt

The frontend sends a request to:

```http
POST /prompts
```

Example request:

```json
{
  "prompt": "Create a modern wooden chair",
  "parameters": {
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
}
```

The `parameters` field is optional.

---

## Step 2 — Flask creates a PromptRequest

When the prompt is accepted, the backend creates a new `PromptRequest`.

Initial status:

```txt
queued
```

Example database state:

```json
{
  "id": 1,
  "prompt_text": "Create a modern wooden chair",
  "parameters": {
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
  },
  "status": "queued",
  "user_id": 1,
  "generated_code": null,
  "result_path": null,
  "error_message": null
}
```

---

## Step 3 — Flask sends the task to Celery

After saving the prompt in the database, the backend queues the task:

```python
process_prompt_task.delay(
    prompt_id=prompt.id,
    parameters=data.get("parameters", {})
)
```

The HTTP request returns quickly with the prompt ID.

The generation work happens in the background.

---

## Step 4 — Redis queues the task

Redis receives the task message from Celery.

The task includes:

```json
{
  "prompt_id": 1,
  "parameters": {
    "size": {
      "width": 1.5,
      "height": 2.0,
      "depth": 1.2
    }
  }
}
```

Redis keeps the task until a Celery worker is available.

---

## Step 5 — Celery worker receives the task

The Celery worker executes:

```python
process_prompt_task(
    prompt_id,
    parameters=None,
    fast_track_id=None,
    imported_asset_id=None
)
```

The task supports three modes:

| Mode | Trigger | Purpose |
|---|---|---|
| `creation` | `POST /prompts` | Create a new 3D asset from a prompt |
| `fast_track_modification` | `POST /prompts/{id}/modify` | Modify a previously generated asset |
| `imported_asset_modification` | `POST /assets/{id}/modify` | Modify an uploaded 3D asset |

---

# 3. Inside `process_prompt_task`

## Step 1 — Create Flask app context

Inside the task, the app is recreated:

```python
from app import create_app

app = create_app()
```

Then the task runs inside:

```python
with app.app_context():
```

This allows the task to use the database and Flask configuration.

---

## Step 2 — Load the PromptRequest

The task retrieves the prompt:

```python
prompt = PromptRequest.query.get(prompt_id)
```

If the prompt does not exist, the task logs an error and stops.

---

## Step 3 — Update status to processing

Before starting the generation, the task updates the prompt status:

```python
prompt.status = PromptStatus.PROCESSING
db.session.commit()
```

This allows the frontend to see that the generation has started.

---

## Step 4 — Initialize the LLM service

The task creates an LLM service:

```python
llm_service = LLMService()
```

`LLMService` reads the configured provider from `config.py`.

Currently, the supported provider is:

```txt
groq
```

If the provider is `groq`, `LLMService` creates a `GroqProvider`.

---

## Step 5 — Choose the generation mode

The task chooses the generation mode depending on the arguments.

### Case 1 — Imported asset modification

If `imported_asset_id` is provided:

```python
generation_mode = "imported_asset_modification"
```

The task builds a prompt that tells the LLM to import and modify an existing 3D file instead of creating a new object from scratch.

### Case 2 — Fast-track modification

If `fast_track_id` is provided:

```python
generation_mode = "fast_track_modification"
```

The task retrieves the previous prompt and asks the LLM to revise the existing Blender Python script.

### Case 3 — New creation

If neither `imported_asset_id` nor `fast_track_id` is provided:

```python
generation_mode = "creation"
```

The task builds a standard generation prompt from the user prompt and optional parameters.

---

# 4. Creation Mode

Creation mode is used for new prompt generation.

## Prompt preparation

The task calls:

```python
_build_generation_prompt(prompt, parameters)
```

This uses:

```python
PromptService.create_final_prompt(...)
```

If parameters are provided and valid, it also calls:

```python
build_llm_prompt(final_user_prompt, validated_params)
```

The parameter schema expects:

```txt
size.width: 0.5 to 5
size.height: 0.5 to 5
size.depth: 0.5 to 5

geometry.complexity: 1 to 10
geometry.smoothness: 1 to 100

material.material_type: Plastic, Metal, Wood or Glass
material.roughness: 0.0 to 1.0
material.metallic: 0.0 to 1.0
```

The prompt service gives the LLM explicit rules, including:

- use `build_chair(...)` for chairs
- use `build_table(...)` for tables/desks
- use `build_tree(...)` for trees/plants
- use primitive shapes for fallback objects
- avoid boolean modifiers
- call `set_material(...)`
- export as GLB

---

# 5. Fast-Track Modification Mode

Fast-track mode is used when modifying a previously generated result.

The frontend calls:

```http
POST /prompts/{id}/modify
```

The backend creates a new `PromptRequest` with:

```txt
parent_prompt_id = original_prompt.id
```

Then it queues the task with:

```python
process_prompt_task.delay(
    prompt_id=new_prompt.id,
    parameters=new_prompt.parameters,
    fast_track_id=original_prompt.id
)
```

Inside Celery, the task loads the previous prompt using `fast_track_id`.

The source prompt must have existing generated code:

```python
source = PromptRequest.query.get(fast_track_id)

if not source or not source.generated_code:
    raise LLMError("Source for fast-track not found or has no code.")
```

Then the LLM receives:

- the modification command
- the updated request or parameters
- the existing Blender Python script

The goal is to revise the existing script rather than generate a completely unrelated one.

---

# 6. Imported Asset Modification Mode

Imported asset modification mode is used when the user uploads an existing `.glb`, `.gltf`, or `.obj` file and asks the system to modify it.

The frontend calls:

```http
POST /assets/{id}/modify
```

The backend creates a new `PromptRequest` with:

```txt
imported_asset_id = asset.id
```

Then it queues the task:

```python
process_prompt_task.delay(
    prompt_id=new_prompt.id,
    parameters={},
    imported_asset_id=asset.id
)
```

Inside Celery, the task retrieves the imported asset:

```python
imported_asset = ImportedAsset.query.get(imported_asset_id)
```

The task builds an LLM prompt containing:

- imported asset file path
- asset metadata
- modification command
- import instructions for `.glb`, `.gltf`, and `.obj`
- safety rules for modifying only mesh objects

The LLM is instructed to:

- import the existing asset
- keep the asset structure
- modify existing mesh objects
- avoid applying materials to lights, cameras, empties or non-mesh objects
- export the final result as GLB

---

# 7. Asset Metadata Extraction

When a user imports a 3D asset, metadata is extracted before creating the `ImportedAsset` record.

The metadata service supports:

| Format | Extraction Method |
|---|---|
| `.obj` | Reads object/group names, vertices and faces |
| `.gltf` | Reads JSON structure |
| `.glb` | Reads binary GLB header and JSON chunk |

The metadata can include:

```json
{
  "original_filename": "chair.glb",
  "extension": ".glb",
  "file_size_bytes": 123456,
  "interpretable": true,
  "objects": ["Node_0"],
  "meshes": ["Mesh_0"],
  "materials": ["Material_0"],
  "object_count": 1,
  "mesh_count": 1,
  "material_count": 1
}
```

If extraction fails, the metadata is marked as not interpretable:

```json
{
  "interpretable": false,
  "error": "Error message"
}
```

---

# 8. LLM Service Flow

## LLMService

`LLMService` chooses the provider based on:

```python
LLM_PROVIDER
```

Currently:

```python
LLM_PROVIDER = "groq"
```

If the provider is `groq`, the service uses `GroqProvider`.

## GroqProvider

`GroqProvider` creates a `ChatOpenAI` client with:

- base URL
- API key
- model
- temperature
- max tokens
- top_p

Then generation is performed using:

```python
response = self.client.invoke([
    ("system", system_prompt),
    ("human", human_prompt),
])
```

The provider returns:

```python
response.content
```

---

# 9. System Prompt

The task loads the system prompt from the configured path.

```python
system_msg = load_system_prompt()
```

The system prompt instructs the LLM to behave as a Blender Python script generator.

Important rules include:

- output only raw executable Python code
- begin with `import bpy, math, bmesh`
- do not output Markdown
- include helper functions for boxes, cylinders, spheres, materials and known objects
- generate Blender-compatible code

---

# 10. Generated Code Validation

After the LLM returns code, the task removes possible Markdown code fences:

```python
generated_code = _strip_code_fences(llm_output)
```

Then it checks that the generated code contains:

```python
import bpy
```

If not, the task fails with:

```txt
Generated code does not contain 'import bpy' - likely malformed.
```

---

# 11. Export Path Preparation

The task creates a unique output filename based on the prompt ID:

```python
output_filename = f"prompt_{prompt_id}.glb"
output_path = f"static/models/{output_filename}"
```

Then it ensures that the generated Blender code exports to this prompt-specific file.

If the generated code still contains the legacy export path:

```python
bpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')
```

it is replaced by the prompt-specific export path.

If no export line exists, the task appends an export line using the generated `output_path`.

Example for `prompt_id = 12`:

```python
bpy.ops.export_scene.gltf(filepath='static/models/prompt_12.glb', export_format='GLB')
```

---

# 12. Blender Execution Flow

Blender execution is handled by the Blender executor.

## Step 1 — Write temporary script

The generated code is written to a temporary script file:

```python
script_filename = write_script(prompt_id, generated_code)
```

The temporary script is stored in:

```txt
/tmp/blender_scripts
```

The filename format is:

```txt
temp_script_<prompt_id>.py
```

The script size is limited to:

```txt
512 KB
```

The file permissions are restricted to owner read/write only.

---

## Step 2 — Find Blender executable

The executor searches for Blender in this order:

1. `BLENDER_PATH` environment variable
2. `blender` available in system `PATH`
3. platform-specific allowlisted locations

If Blender is not found, the task fails with:

```txt
Blender executable not found. Set BLENDER_PATH in your .env file.
```

---

## Step 3 — Run Blender in background mode

Blender is launched with:

```python
subprocess.run(
    [blender_path, "--background", "--python", script_filename],
    capture_output=True,
    text=True,
    timeout=timeout
)
```

The current timeout is:

```txt
120 seconds
```

---

## Step 4 — Validate Blender result

After Blender finishes, the executor checks:

1. Blender return code is `0`
2. the expected output file exists
3. the output extension is allowed

Allowed output extensions are:

```txt
.glb
.gltf
.blend
.png
.obj
.fbx
```

If the output file was not created, the task fails with:

```txt
Blender ran but output file was not created
```

---

## Step 5 — Store result in database

If Blender succeeds, the task updates the prompt:

```python
prompt.status = PromptStatus.COMPLETED
prompt.result_path = f"/static/models/{output_filename}"
db.session.commit()
```

Example:

```json
{
  "status": "completed",
  "result_path": "/static/models/prompt_1.glb"
}
```

---

## Step 6 — Cleanup temporary script

At the end of the task, the temporary script is removed:

```python
finally:
    cleanup_file(script_filename)
```

This happens even if the task fails.

---

# 13. Error Handling

The task handles several types of errors.

## ConfigurationError

Used for missing or invalid configuration.

Example:

```txt
System prompt file not found
```

Behavior:

```txt
status = failed
error_message = configuration error
```

---

## LLMError

Used when the LLM call fails or returns malformed code.

Example causes:

- missing API key
- invalid model
- provider error
- generated code does not contain `import bpy`
- source prompt missing in fast-track mode
- imported asset file missing

The task sets the prompt as failed and retries the task.

Celery retry configuration:

```python
max_retries = 2
default_retry_delay = 10
```

---

## BlenderExecutionError

Used when Blender fails.

Example causes:

- Blender executable not found
- Blender timeout
- generated script error
- non-zero Blender return code
- output file not created

Behavior:

```txt
status = failed
error_message = Blender error
```

---

## Unexpected Exception

For any unexpected error, the task:

1. stores the traceback in logs
2. stores a short error message in the database
3. marks the prompt as failed
4. retries if possible

---

# 14. Database Status Updates

The database is the source of truth for frontend status.

The frontend does not communicate directly with Celery.

Instead, it polls:

```http
GET /prompts/{id}
```

Possible statuses:

| Status | Meaning |
|---|---|
| `queued` | Task was created and is waiting for Celery |
| `processing` | Celery worker is processing the task |
| `completed` | Generation completed successfully |
| `failed` | Generation failed |
| `ambiguous` | Prompt is ambiguous |
| `awaiting_clarification` | Prompt needs more details |
| `invalid` | Prompt is invalid |

---

# 15. Frontend Polling Flow

## Step 1 — Submit prompt

```http
POST /prompts
```

The backend returns:

```json
{
  "id": 1,
  "status": "queued"
}
```

## Step 2 — Poll prompt status

```http
GET /prompts/1
```

While queued:

```json
{
  "id": 1,
  "status": "queued",
  "result_path": null,
  "error_message": null
}
```

While processing:

```json
{
  "id": 1,
  "status": "processing",
  "result_path": null,
  "error_message": null
}
```

After success:

```json
{
  "id": 1,
  "status": "completed",
  "result_path": "/static/models/prompt_1.glb",
  "error_message": null
}
```

After failure:

```json
{
  "id": 1,
  "status": "failed",
  "result_path": null,
  "error_message": "Blender exited with a non-zero return code."
}
```

---

# 16. Troubleshooting

## Prompt stays in queued

Possible causes:

- Redis is not running
- Celery worker is not running
- Celery worker was started with the wrong command
- task module was not imported
- Flask and Celery are not using the same Redis URL

Check Redis:

```bash
redis-cli ping
```

Expected response:

```txt
PONG
```

Start worker:

```bash
celery -A worker.celery worker --loglevel=info
```

---

## Task is not registered

Possible causes:

- `app.tasks.prompt_tasks` is not imported in `worker.py`
- wrong Celery app path in the command
- worker started from the wrong directory

Expected import in `worker.py`:

```python
import app.tasks.prompt_tasks
```

---

## LLM call fails

Possible causes:

- missing `LLM_API_KEY`
- invalid `LLM_BASE_URL`
- invalid `LLM_MODEL`
- unsupported `LLM_PROVIDER`
- API/network issue

Check:

```txt
.env
config.py
Celery logs
PromptRequest.error_message
```

---

## Generated code is malformed

Possible causes:

- LLM returned Markdown instead of raw Python
- LLM did not include `import bpy`
- LLM ignored the system prompt
- output was truncated

The task validates that the generated code contains:

```python
import bpy
```

If not, the task fails and stores an error message.

---

## Blender execution fails

Possible causes:

- Blender is not installed
- `BLENDER_PATH` is missing or incorrect
- generated script contains invalid Blender Python
- script timeout
- output file was not created

Check:

```txt
BLENDER_PATH
Celery logs
PromptRequest.generated_code
PromptRequest.error_message
static/models
```

---

## Output file is not accessible

Possible causes:

- prompt status is not `completed`
- `result_path` is missing
- file was not created
- file path is incorrect
- user is not authenticated
- user does not own the prompt

Relevant endpoints:

```http
GET /prompts/{id}/file
```

```http
GET /prompts/{id}/download
```

---

# 17. Summary

The asynchronous architecture works as follows:

1. The frontend submits a prompt to Flask.
2. Flask validates the request and creates a `PromptRequest`.
3. Flask queues a Celery task using Redis.
4. Redis stores the task until a worker is available.
5. Celery processes the task in the background.
6. The task prepares the LLM prompt.
7. The LLM generates Blender Python code.
8. The generated code is validated and written to a temporary script.
9. Blender runs the script in background mode.
10. A GLB file is exported.
11. The database is updated with the final status and result path.
12. The frontend polls the API until the task is completed or failed.

This architecture keeps the API responsive and separates heavy generation work from normal HTTP request handling.