# SUNRISE Project

AI-powered platform for generating and interacting with 3D assets using natural language.

---

## Overview

SUNRISE is a web-based system that enables users to generate, preview, refine, and modify 3D models from simple text prompts.

The platform combines:
- Large Language Models (LLMs) for understanding user intent
- Blender (`bpy`) for procedural 3D generation
- A modern web interface for interaction and visualization
- PostgreSQL for persistent storage and shared collaboration

---

## Features

- AI-powered 3D generation from text prompts
- Blender Python (`bpy`) procedural asset generation
- Asset refinement and modification workflow
- Prompt versioning system
- Authentication and user access control
- Shared PostgreSQL database
- Feedback and analytics system
- Power BI export support
- Celery asynchronous processing
- Modular LLM provider architecture
- Benchmarking and evaluation tools
- Configurable LLM generation parameters for tuning output quality

---

## Tech Stack

### Backend
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Celery
- Redis
- PostgreSQL

### Frontend
- Next.js
- React
- TypeScript

### AI & 3D
- Groq API / LLM
- Blender (`bpy`)
- GLTF / GLB export

---

## Architecture

The system follows a modular layered architecture:

```text
User
  ↓
Frontend (Next.js)
  ↓
Backend API (Flask)
  ↓
Celery Task Queue
  ↓
LLM Service Layer
  ↓
Validation Layer
  ↓
Blender Execution
  ↓
GLB Export
  ↓
PostgreSQL Storage
```

### Components

- Frontend — user interface, interaction and preview
- Backend — orchestration, APIs and processing
- LLM Layer — prompt interpretation and code generation
- Validation Layer — script validation and safety checks
- Blender Engine — procedural 3D generation
- PostgreSQL Database — persistent storage for users, prompts, feedback and analytics

---

## Project Structure

```text
SUNRISE_PROJECT/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── tasks/
│   ├── static/
│   ├── extensions.py
│   ├── celery_app.py
│   └── __init__.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── services/
│   ├── state/
│   └── package.json
│
├── migrations/
├── tests/
├── config.py
├── requirements.txt
├── run.py
├── worker.py
└── README.md
```

---

# Local Setup & Execution Guide

This guide explains how to configure and run the full generation pipeline locally.

---

## Requirements

Before starting, install:

### Required Software
- Python 3.10+
- Node.js v20+
- PostgreSQL
- Redis
- Blender

### Blender
Download Blender from:
- https://www.blender.org/download/

### PostgreSQL
Download PostgreSQL from:
- https://www.postgresql.org/download/

### Redis
You may use:
- Redis Server
- Memurai
- Docker Redis container

---

# PART 1 — FIRST TIME SETUP

## 1. Clone Repository

```bash
git clone <repository-url>
cd SUNRISE_PROJECT
```

---

## 2. Create Python Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows
```bash
venv\Scripts\activate
```

### Linux / Mac
```bash
source venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure PostgreSQL

If you are hosting the shared database, create the PostgreSQL database:

```sql
CREATE DATABASE bip_shared_db;
```

If you are a team member using the shared database:
- do not create a local database
- ask the database host for the shared `DATABASE_URL`

---

## 5. Configure Environment Variables

Copy `.env.example` into `.env`.

Example configuration:

```env
SECRET_KEY=your_secret_key

DATABASE_URL=postgresql://postgres:password@HOST_IP:5432/bip_shared_db

LLM_API_KEY=your_groq_api_key

LLM_PROVIDER=groq
LLM_TEMPERATURE=0.2
LLM_TOP_P=0.9
LLM_MAX_TOKENS=1200

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 6. Run Database Migrations

```bash
flask db upgrade
```

---

## 7. Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

# PART 2 — DAILY RUN

The application requires:
- Backend server
- Celery worker
- Frontend server
- Redis server

All services must run simultaneously.

---

## Step 0 — Start Redis

### Option A — Redis Installed Locally
Ensure Redis service is running.

### Option B — Docker Redis

```bash
docker run -p 6379:6379 -d redis
```

---

## Terminal 1 — Backend Server

```bash
venv\Scripts\activate
python run.py
```

Backend runs on:

```text
http://127.0.0.1:5000
```

---

## Terminal 2 — Celery Worker

```bash
venv\Scripts\activate
celery -A worker.celery worker --loglevel=info --pool=solo
```

---

## Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

Frontend runs on:

```text
http://localhost:3000
```

---

# Shared Database

The project uses a shared PostgreSQL database architecture.

This allows:
- shared prompt history
- synchronized generated assets
- centralized feedback analytics
- multi-user support
- deployment-ready infrastructure

Each team member must configure the same `DATABASE_URL`.

Example:

```env
DATABASE_URL=postgresql://postgres:password@HOST_IP:5432/bip_shared_db
```

---

# Testing

Go to:

```text
http://localhost:3000
```

Example prompt:

```text
A wooden table with metal legs
```

Check the Celery terminal to verify:
- task processing
- Blender execution
- GLB export generation

---

# Benchmarking Methodology

The benchmarking module evaluates generated 3D assets using predefined test prompts and scoring metrics.

## Evaluation Categories

Each generated asset is scored from 0 to 10 using:

| Metric | Description |
|---|---|
| Compliance | Match between prompt and generated asset |
| Stability | Absence of artifacts or disconnected meshes |
| Geometry Quality | Mesh topology and normals |
| Materials | Quality and correctness of shaders/materials |
| Blender Success | Reliability during Blender execution |
| Final Export | Usability of exported GLB/GLTF |

---

## LLM Configuration Parameters

The LLM generation behavior can be adjusted through environment variables.

| Variable | Default | Description |
|---|---:|---|
| LLM_TEMPERATURE | 0.2 | Controls randomness. Lower values produce more stable outputs. |
| LLM_TOP_P | 0.9 | Controls nucleus sampling and limits token selection to likely candidates. |
| LLM_MAX_TOKENS | 1200 | Controls maximum generated output length. |

Recommended configuration for stable Blender generation:

```env
LLM_TEMPERATURE=0.2
LLM_TOP_P=0.9
LLM_MAX_TOKENS=1200
```
```md
After changing LLM parameters in `.env`, restart both the backend server and Celery worker.
```

## Adding a New Benchmark Test

### 1. Add a Test Prompt

Register a new `TestPrompt` inside `TEST_PROMPTS`.

### 2. Add Evaluation Scores

Add scoring data inside:
- `build_sample_report()`
- or external JSON evaluation files

### 3. Run Dashboard

```bash
python run_dashboard.py
```

---

# Troubleshooting

## Redis Connection Error

If Celery cannot connect:

```text
Connection refused
Cannot connect to Redis
```

Ensure Redis server is running.

---

## CORS Errors

Verify frontend API URL matches:
- localhost
- or 127.0.0.1

---

## PostgreSQL Connection Error

Verify:
- PostgreSQL service is running
- database exists
- `.env` DATABASE_URL is correct

---

## Migration Issues

If migrations fail:

```bash
flask db stamp head
flask db upgrade
```

---

# Security Notes

- Never commit `.env`
- Never expose API keys publicly
- Never share PostgreSQL credentials
- Use environment variables for all secrets

---

# Future Improvements


---

# Authors

SUNRISE Project Team

International collaborative project focused on AI-assisted 3D generation systems.
