# Frontend Architecture Guide

## Overview

The frontend is a Next.js application for creating, previewing, modifying, importing, downloading, and evaluating 3D assets. It is intentionally thin on generation logic: the browser collects user input, manages UI state, calls the backend API, polls asynchronous jobs, and renders the returned 3D files.

The application lives in:

```txt
frontend/
```

Core technologies:

- Next.js App Router
- React client components
- TypeScript
- Tailwind CSS
- Zustand for client state
- Three.js through `@react-three/fiber` and `@react-three/drei`
- Recharts for feedback analytics

---

## 1. Application Structure

Important frontend folders:

| Path | Purpose |
|---|---|
| `frontend/app/` | App Router pages, root layout, global CSS |
| `frontend/components/` | Reusable UI and workflow components |
| `frontend/services/` | API and generation service helpers |
| `frontend/state/` | Zustand stores for shared client state |
| `frontend/public/` | Static assets, logo, and demo 3D models |
| `frontend/tests/` | Frontend test assets or future frontend tests |

Important pages:

| Page | File | Purpose |
|---|---|---|
| Main workspace | `app/page.tsx` | Prompt input, parameters, preview, import, modify, feedback, history drawer |
| History | `app/history/page.tsx` | Full prompt history page |
| Analytics | `app/analytics/page.tsx` | Feedback analytics dashboard |
| Root layout | `app/layout.tsx` | App metadata, fonts, and global service status boundary |

---

## 2. High-Level Runtime Flow

The main generation path is:

1. The user authenticates through the login or signup modal.
2. The user enters a prompt and adjusts model parameters.
3. `GenerateButton` validates the prompt and formats parameters.
4. `services/api.ts` sends `POST /prompts` to the backend.
5. The backend returns a prompt ID.
6. The frontend polls `GET /prompts/{id}` until completion or failure.
7. The completed result is stored in the generation store.
8. The preview loads the generated model from `GET /prompts/{id}/file`.
9. Download, feedback, modification, and history controls become available.

The frontend never generates final model geometry locally. Local model analysis is used only for metadata extraction and UI display.

---

## 3. State Management

Shared client state is stored with Zustand.

### `state/generationStore.ts`

This store owns the active creation workspace:

- prompt text;
- modification command;
- model parameters;
- generation status;
- current result;
- current imported asset;
- user-facing error message.

Generation statuses:

```txt
idle
submitted
processing
success
error
```

Default parameters:

- size: width, height, depth;
- geometry: complexity and smoothness;
- material: plastic, roughness, metallic.

### `state/authStore.ts`

This store keeps the currently authenticated user in memory:

- user ID;
- username;
- email.

Authentication is still backend-session based. The store mirrors the currently known user so the UI can unlock protected actions.

### `state/serviceStatusStore.ts`

This store tracks backend availability:

- `available`;
- `unavailable`;
- optional message shown in the service unavailable overlay.

It is updated by the shared API client when network requests fail or return gateway/service errors.

---

## 4. API Layer

The main integration file is:

```txt
frontend/services/api.ts
```

Responsibilities:

- build requests from `NEXT_PUBLIC_API_BASE_URL`;
- include session cookies for authenticated endpoints;
- parse JSON responses safely;
- normalize backend errors into stable frontend messages;
- mark the backend unavailable on network failures and `502`, `503`, or `504`;
- create prompts and poll prompt status;
- upload imported assets with progress;
- fetch preview blobs and download URLs;
- submit feedback and load analytics.

The default local API base URL is:

```txt
http://localhost:5000
```

The configured value comes from:

```txt
NEXT_PUBLIC_API_BASE_URL
```

Because this is a `NEXT_PUBLIC_*` variable, it must never contain secrets.

---

## 5. Backend Communication Patterns

### Session Authentication

The frontend uses cookie-based sessions. Authenticated API calls include:

```ts
credentials: "include"
```

Auth endpoints:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

### Asynchronous Generation

Prompt generation is job-based:

- create job with `POST /prompts`;
- poll job with `GET /prompts/{id}`;
- treat `queued` and `processing` as active states;
- treat `completed` as success;
- treat `failed` as an error.

Polling currently waits two seconds between status checks.

### Files

Generated model files are loaded through:

- `GET /prompts/{id}/file` for preview and metadata extraction;
- `GET /prompts/{id}/download` for download links.

### Imported Assets

Asset import uses `XMLHttpRequest` instead of `fetch` because the UI needs upload progress.

Endpoints:

- `POST /assets/import`
- `GET /assets/{id}/metadata`
- `POST /assets/{id}/modify`

Supported import formats:

```txt
GLB
GLTF
OBJ
```

---

## 6. Main Components

| Component | Responsibility |
|---|---|
| `GenerateButton` | Validates prompt, formats parameters, triggers generation, updates generation state |
| `ParameterPanel` | Lets users control size, geometry, and material values |
| `PreviewCanvas` | Renders GLB, GLTF, or OBJ models with Three.js and orbit controls |
| `ImportAssetPanel` | Handles file selection, drag and drop, validation, upload progress, and import result state |
| `HistoryPanel` | Loads prompt history, supports search, sorting, version expansion, and version selection |
| `FeedbackWidget` | Collects quality and accuracy scores plus optional comments |
| `AuthModal` | Handles login and signup |
| `GuidedTour` | Explains key workspace controls to new users |
| `ServiceStatusBoundary` | Mounts global backend-unavailable fallback UI |
| `ServiceUnavailableScreen` | Shows retry flow when the backend cannot be reached |

---

## 7. 3D Preview Architecture

The preview is implemented in:

```txt
frontend/components/PreviewCanvas.tsx
```

It uses:

- `Canvas` from `@react-three/fiber`;
- `useGLTF` for GLB and GLTF files;
- `OBJLoader` for OBJ files;
- `Center` from `@react-three/drei` to center loaded models;
- `OrbitControls` for rotation and zoom.

The preview can render:

- backend-generated models;
- imported local assets;
- demo models from `frontend/public/models/`.

The main page creates object URLs for fetched blobs and revokes old local URLs when the active asset changes.

---

## 8. Metadata Handling

Metadata can come from the backend or from lightweight frontend analysis.

Backend metadata is used for imported assets through:

```txt
GET /assets/{id}/metadata
```

Frontend metadata extraction is used for previewed files when needed:

- OBJ: reads object/group names, vertices, and faces;
- GLTF: parses JSON nodes, meshes, and materials;
- GLB: reads the JSON chunk and extracts similar structure information.

The metadata panel displays:

- file extension;
- file size;
- object count;
- object and mesh structure;
- material names when available.

For imported assets, the frontend can derive starting parameters from metadata so modification requests have reasonable defaults.

---

## 9. History and Versioning

Prompt history is loaded from:

```txt
GET /prompts/me
```

Detailed prompt and version data is loaded from:

```txt
GET /prompts/{id}
```

The history UI supports:

- logged-out empty state;
- loading and error states;
- search by prompt, status, path, modification command, and ID;
- newest/oldest sorting;
- expandable version history;
- selecting a previous version back into the active workspace.

Modified models are represented as new prompt versions rather than overwriting the original prompt.

---

## 10. Feedback and Analytics

Feedback is submitted from the generated-model workflow:

```txt
POST /prompts/{id}/feedback
```

The widget records quality and accuracy scores from 1 to 5. It maps the quality score into a backend rating:

- 4-5: `positive`;
- 3: `neutral`;
- 1-2: `negative`.

The widget stores a local submitted marker per prompt ID to avoid repeated submissions in the same browser. The backend remains the source of truth and can still reject duplicate feedback.

Analytics are loaded from:

```txt
GET /prompts/feedback/analytics
```

The analytics page renders:

- total feedback count;
- success rate;
- average accuracy;
- average quality;
- rating mix pie chart;
- average score bar chart;
- optional user comments list.

---

## 11. Error and Availability Strategy

The frontend uses a centralized error strategy in `services/api.ts`.

Backend errors are normalized into codes such as:

- `AUTH_REQUIRED`;
- `AUTH_INVALID`;
- `EMAIL_IN_USE`;
- `VALIDATION_FAILED`;
- `PROMPT_BLOCKED`;
- `ASSET_UNSUPPORTED`;
- `ASSET_UNINTERPRETABLE`;
- `DUPLICATE_FEEDBACK`;
- `BACKEND_UNAVAILABLE`;
- `UNKNOWN`.

These codes are converted into user-friendly messages before being shown in components.

Backend availability is handled globally. When a request fails due to a network problem or returns `502`, `503`, or `504`, the API layer marks the service unavailable. `ServiceStatusBoundary` then displays `ServiceUnavailableScreen` over the current page.

The retry button checks:

```txt
GET /
```

When the backend responds successfully, the overlay closes.

---

## 12. Local Development

Run commands from `frontend/`.

Install dependencies:

```bash
npm install
```

Start the backend from the repository root:

```bash
python run.py
```

Start the frontend:

```bash
npm run dev
```

Build production output:

```bash
npm run build
```

Run lint:

```bash
npm run lint
```

---

## 13. Architectural Guidelines

Use these rules when extending the frontend:

1. Keep backend communication inside `services/api.ts` unless a new service file clearly owns a separate domain.
2. Keep shared workflow state in Zustand stores and local UI-only state inside components.
3. Use the existing prompt polling pattern for any backend operation that creates asynchronous generation work.
4. Keep auth-protected UI clear, but rely on the backend as the final authorization boundary.
5. Reuse normalized backend errors instead of showing raw response messages.
6. Keep Three.js loading logic inside preview-focused components.
7. Keep documentation in `docs/` updated when changing flows, endpoints, or user-visible behavior.

---

## Summary

The frontend architecture is a client-side Next.js workspace with a centralized API layer, small Zustand stores, workflow-focused React components, Three.js preview rendering, and global backend availability handling. The backend remains responsible for authentication, generation, persistence, file storage, and analytics, while the frontend provides the interactive user experience around those capabilities.
