# Frontend API and Backend Integration

## Overview

This document explains how the frontend communicates with the backend API. The frontend is responsible for collecting user input, sending requests to the backend, waiting for asynchronous generation results, loading generated files, and showing clear user-facing messages when something fails.

The main API integration code is located in:

```txt
frontend/services/api.ts
```

This file centralizes backend communication so that components do not need to repeat request logic.

---

## 1. API Base URL

The frontend reads the backend URL from:

```txt
NEXT_PUBLIC_API_BASE_URL
```

Local example:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
```

If this variable is not configured, the frontend falls back to:

```txt
http://localhost:5000
```

The API client removes trailing slashes from the configured URL. This prevents duplicated slashes when endpoint paths are appended.

Important note: `NEXT_PUBLIC_*` variables are exposed to the browser, so this variable must not contain secrets, private keys, or database credentials.

---

## 2. Shared API Request Handling

Most backend requests go through a shared wrapper in `api.ts`.

The shared request logic is responsible for:

- adding the backend base URL;
- sending HTTP requests with the correct options;
- detecting backend-unavailable responses;
- parsing JSON responses;
- converting backend errors into readable frontend errors;
- keeping API behavior consistent across the application.

Backend-unavailable responses include:

```txt
502
503
504
```

Network failures are handled in the same flow. When the backend cannot be reached, the frontend updates the service status state and shows the service unavailable screen.

---

## 3. Authentication Integration

The backend uses session-based authentication. After login or signup, the backend stores the user session in a cookie.

For authenticated requests, the frontend sends:

```txt
credentials: include
```

This allows browser cookies to be included in requests to the backend.

Authentication endpoints used by the frontend:

| Frontend action | Backend endpoint | Purpose |
|---|---|---|
| Sign up | `POST /auth/signup` | Create a new user account |
| Log in | `POST /auth/login` | Authenticate the user |
| Get current user | `GET /auth/me` | Check the active session |
| Log out | `POST /auth/logout` | End the active session |

After successful login or signup, the frontend stores the returned user information in the authentication state. This user state controls access to generation, importing, feedback, and history features.

---

## 4. Prompt Generation Integration

The main generation flow starts when the user enters a prompt, adjusts parameters, and clicks the generate button.

The frontend sends the generation request to:

```http
POST /prompts
```

The request contains:

- prompt text;
- size parameters;
- geometry parameters;
- material parameters.

Example payload:

```json
{
  "prompt": "Create a wooden table",
  "parameters": {
    "size": {
      "width": 1,
      "height": 1,
      "depth": 1
    },
    "geometry": {
      "complexity": 5,
      "smoothness": 50
    },
    "material": {
      "material_type": "Wood",
      "roughness": 0.5,
      "metallic": 0.2
    }
  }
}
```

The backend does not return the finished model immediately. Instead, it creates a prompt request, queues background processing, and returns a prompt ID.

The frontend then polls:

```http
GET /prompts/{id}
```

Polling continues while the prompt status is:

```txt
queued
processing
```

When the status becomes `completed`, the frontend loads the generated model. If the status becomes `failed`, the frontend shows a user-friendly error.

Main frontend functions:

| Function | Responsibility |
|---|---|
| `createPrompt` | Sends the prompt and parameters to the backend |
| `pollPrompt` | Repeatedly checks generation status |
| `generateModel` | Combines prompt creation and polling |

---

## 5. Generated Model File Integration

After successful generation, the frontend uses backend file endpoints to display or download the result.

| Frontend action | Backend endpoint | Purpose |
|---|---|---|
| Preview model | `GET /prompts/{id}/file` | Load generated file into the 3D preview |
| Download model | `GET /prompts/{id}/download` | Download the generated GLB file |

The preview endpoint is used by the 3D viewer. The download endpoint is used by the download button after a model is ready.

---

## 6. Model Modification Integration

Generated models can be refined with a modification command.

The frontend sends modification requests to:

```http
POST /prompts/{id}/modify
```

Example command:

```txt
Make the chair taller and change the material to metal.
```

The backend creates a new prompt version and returns the new prompt ID. The frontend polls this new ID until the modified model is completed.

This keeps the original generated model available and allows the system to show version history.

---

## 7. Imported Asset Integration

The frontend supports importing existing 3D assets.

Supported file formats:

```txt
GLB
GLTF
OBJ
```

The upload request is sent to:

```http
POST /assets/import
```

The upload uses `XMLHttpRequest` instead of normal `fetch` because the UI displays upload progress.

After upload, the frontend loads metadata from:

```http
GET /assets/{id}/metadata
```

The metadata can include:

- original filename;
- file type;
- file size;
- objects;
- materials;
- object count.

To modify an imported asset, the frontend sends:

```http
POST /assets/{id}/modify
```

The backend creates a prompt request connected to the imported file. The frontend then uses the same polling approach as normal generation.

---

## 8. Prompt History Integration

The prompt history feature uses backend endpoints to load previous user generations.


Load my prompts - `GET /prompts/me` - Fetch the current user's prompt history 
Load prompt details - `GET /prompts/{id}` - Fetch prompt details and version history 
Rename prompt - `PATCH /prompts/{id}` - Update prompt display text 
Delete prompt - `DELETE /prompts/{id}` - Remove a prompt and related versions 

History is user-specific, so these requests require an authenticated session.

---

## 9. Feedback and Analytics Integration

The frontend allows users to submit feedback for generated results.

Feedback is sent to:

```http
POST /prompts/{id}/feedback
```

The feedback payload can include:

- rating: `positive`, `neutral`, or `negative`;
- accuracy score;
- quality score;
- optional comment.

The analytics page loads aggregated feedback data from:

```http
GET /prompts/feedback/analytics
```

The frontend displays:

- total feedback count;
- success rate;
- average accuracy score;
- average quality score;
- rating distribution;
- user comments.

---

## 10. Backend Availability Check

When the backend is unavailable, the frontend shows a service unavailable screen.

The retry action checks:

```http
GET /
```

If the backend responds successfully, the frontend marks the service as available and closes the overlay.

This is important because the application depends on the backend for authentication, generation, uploads, history, and analytics.

---

## 11. Error Handling

The frontend normalizes backend errors into stable user-facing messages.

Examples of handled cases:

- user is not authenticated;
- login credentials are invalid;
- email is already used;
- prompt validation fails;
- generated model fails;
- imported file format is unsupported;
- imported asset cannot be interpreted;
- feedback was already submitted;
- backend is unavailable.

This keeps the UI clear and prevents raw technical backend errors from being shown directly to the user.

---

## Summary

The frontend communicates with the backend through a centralized API service. The most important integration patterns are:

1. Authenticated requests use session cookies.
2. Generation is asynchronous, so the frontend creates a prompt and polls for completion.
3. Generated files are loaded from backend file endpoints.
4. Imported assets use upload progress and metadata loading.
5. Prompt history and version history are loaded from backend prompt endpoints.
6. Feedback and analytics are connected through backend feedback endpoints.
7. Backend connection problems are handled with a global unavailable screen.

This makes the frontend API layer reusable, predictable, and easier to maintain.
