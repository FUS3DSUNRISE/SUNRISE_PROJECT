# 🌅 SUNRISE Project

AI-powered platform for generating and interacting with 3D assets using natural language.

---

## 📌 Overview

SUNRISE is a web-based system that enables users to generate, preview, and refine 3D models from simple text prompts.

The platform combines:
- Large Language Models (LLMs) for understanding user intent
- Blender (`bpy`) for procedural 3D generation
- A modern web interface for interaction and visualization

---

## 🏗 Architecture

The system follows a modular, layered architecture:

`User → Frontend → Backend → LLM → bpy Script → Blender → 3D Asset → Preview`

### Components

- **Frontend** — user interface, preview, interaction
- **Backend** — orchestration, API, processing
- **LLM Layer** — prompt interpretation and code generation
- **Validation Layer** — script safety and correctness
- **Blender Engine** — 3D asset generation
- **Storage (future)** — history and reproducibility

---

## 📁 Project Structure

```text
SUNRISE_PROJECT/
├── app/                     # Backend (Flask)
├── config.py
├── run.py
├── requirements.txt
│
├── frontend/                # Frontend (Next.js)
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── public/
│   ├── services/
│   ├── state/
│   ├── types/
│   └── package.json
│
└── README.md
