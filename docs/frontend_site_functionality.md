# Frontend Site Functionality

## Overview

This document describes how the frontend site works from the user's point of view. It focuses on the main user workflows and how the interface behaves while communicating with the backend.

The frontend is a workspace where users can create, preview, modify, import, and evaluate 3D models. The frontend does not generate the final model by itself. It sends user input to the backend, waits for the backend processing result, and displays the generated file when it is ready.

---

## 1. Main User Goal

The main goal of the site is to let users create 3D models from text prompts.

A typical user journey is:

1. The user logs in or signs up.
2. The user writes a prompt describing a 3D object.
3. The user adjusts model parameters.
4. The user starts generation.
5. The frontend waits while the backend processes the request.
6. The generated model appears in the 3D preview.
7. The user can download the result or modify it further.

This workflow gives the user a complete loop from idea to downloadable 3D asset.

---

## 2. Authentication Flow

The user needs an account for the main system features.

Authentication flow:

1. The user opens the site.
2. The user chooses login or signup.
3. The authentication modal collects email and password.
4. The frontend sends the request to the backend.
5. If the request succeeds, the frontend stores the logged-in user.
6. Features that require authentication become available.

Authentication is required for:

- generating a model;
- importing a 3D asset;
- viewing prompt history;
- downloading user-specific generated files;
- submitting feedback.

If the user tries to use a protected feature without logging in, the frontend shows a clear message. Some features are locked directly in the UI, such as asset import. For generation requests, authentication is enforced by the backend. If an unauthenticated generation request is sent, the backend rejects it with `401 Unauthorized`, and the frontend maps that response to `AUTH_REQUIRED` and shows:

```txt
Please log in before continuing.
```

---

## 3. Prompt and Parameter Input

The main page lets the user describe the model with a text prompt.

The user can also configure structured parameters:

- width;
- height;
- depth;
- complexity;
- smoothness;
- material type;
- roughness;
- metallic value.

These parameters help the backend create a more controlled generation request. The frontend formats the values before sending them to the backend.

Before generation starts, the frontend validates that the prompt has a maximum length of 120 characters.

If this check fails, the frontend shows an error message and does not send the generation request.

Forbidden character validation and content safety validation are handled by the backend. Backend `400` prompt errors are mapped to `PROMPT_BLOCKED` and shown to the user as:

```txt
This prompt cannot be generated. Please revise the request and try again.
```

---

## 4. Generation Flow

When the user clicks the generate button, the frontend changes the UI state and starts the generation workflow.

Generation flow:

1. The frontend validates the prompt and parameters.
2. The frontend sends the generation request to the backend.
3. The backend returns a prompt ID.
4. The frontend starts polling the prompt status.
5. While the backend is working, the UI shows submitted or processing state.
6. When the backend returns `completed`, the result is shown.
7. If the backend returns `failed`, the frontend displays an error message.

The frontend uses these user-facing states:

| UI state | Meaning |
|---|---|
| `idle` | No generation is running |
| `submitted` | The request was sent |
| `processing` | The backend is working |
| `success` | The model is ready |
| `error` | Generation or validation failed |

This keeps the user informed during a process that may take time.

---

## 5. 3D Preview Flow

After a model is ready, the frontend displays it in an interactive 3D preview.

The preview allows the user to:

- rotate the model;
- zoom in and out;
- inspect the shape and material visually;
- compare generated, imported, or demo models.

Generated models are loaded from the backend. Demo models are loaded from frontend public assets. Imported models can also be previewed after upload.

The preview is an important part of the site because it lets the user check the result before downloading or modifying it.

---

## 6. Download Flow

When generation succeeds, the frontend shows a download option.

Download flow:

1. The backend completes the model generation.
2. The frontend receives the generated prompt result.
3. The page shows a download link.
4. The user downloads the generated GLB file from the backend.

This allows the generated model to be reused outside the web application.

---

## 7. Model Modification Flow

The user can improve a generated model without starting from zero.

Modification flow:

1. A generated model is active in the preview.
2. The user writes a modification command.
3. The frontend sends the command to the backend.
4. The backend creates a new version of the prompt.
5. The frontend polls the new version until it is completed.
6. The modified model becomes the active preview.

Example modification commands:

```txt
Make it taller.
Change the material to metal.
Make the shape smoother.
Add more detail to the object.
```

This workflow supports iterative creation. The user can generate a first version and then refine it step by step.

---

## 8. Imported Asset Flow

The site also supports importing existing 3D files.

Import flow:

1. The user opens the import panel.
2. The user selects or drops a supported file.
3. The frontend validates the file extension.
4. The file uploads to the backend.
5. The UI shows upload progress.
6. The frontend loads metadata after upload.
7. The imported asset can be previewed.
8. The user can send a modification command for the imported asset.

Supported formats:

```txt
GLB
GLTF
OBJ
```

If the file cannot be interpreted, the frontend shows an error. This prevents the user from continuing with a broken or unsupported asset.

---

## 9. Prompt History Flow

The history feature helps users return to previous generations.

History flow:

1. The user opens the history panel or history page.
2. The frontend loads saved prompts for the authenticated user.
3. The user can search and sort prompts.
4. The user can expand a prompt to see versions.
5. The user can select a previous version.
6. The selected result is loaded back into the active workspace.

The history feature is connected to modifications because modified results are stored as prompt versions.

---

## 10. Feedback Flow

After reviewing a generated model, the user can submit feedback.

Feedback flow:

1. The user views a generated result.
2. The user selects a rating.
3. The user can add accuracy and quality scores.
4. The user can write an optional comment.
5. The frontend sends the feedback to the backend.

This feedback helps evaluate the quality and usefulness of generated models.

---

## 11. Analytics Flow

The analytics page displays feedback statistics.

The page shows:

- total feedback count;
- success rate;
- average accuracy score;
- average quality score;
- rating distribution;
- written comments.

The frontend loads this data from the backend and renders it as dashboard-style information.

---

## 12. Backend Unavailable Flow

The site has a fallback for backend connection problems.

If the backend cannot be reached, the frontend shows a service unavailable screen. The user can click retry, and the frontend checks whether the backend is available again.

This prevents confusing silent failures and gives the user a clear recovery action.

---

## Summary

The frontend site provides the main user-facing workflow for the 3D generation system:

1. authenticate the user;
2. collect prompt and parameter input;
3. send generation requests to the backend;
4. wait for asynchronous backend processing;
5. preview the generated model;
6. allow downloading;
7. support model modification;
8. support imported assets;
9. provide prompt history;
10. collect feedback;
11. show analytics;
12. handle backend availability problems.

Together, these flows make the site usable as a complete interface for generating and managing 3D assets.
