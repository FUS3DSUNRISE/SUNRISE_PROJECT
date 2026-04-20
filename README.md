# SUNRISE Project

AI-powered platform for generating and interacting with 3D assets using natural language.

---

## Overview

SUNRISE is a web-based system that enables users to generate, preview, and refine 3D models from simple text prompts.

The platform combines:
- Large Language Models (LLMs) for understanding user intent
- Blender (`bpy`) for procedural 3D generation
- A modern web interface for interaction and visualization

---

## Architecture

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

Local Setup & Execution Guide

This guide explains how to configure and run the End-to-End generation pipeline locally.

### Requirements (Before you start)

  * **Python (3.10+)**: ⚠️ **IMPORTANT:** During installation, you must check the box `"Add Python.exe to PATH"`.
  * **Node.js (v20+)**: Required for the frontend.
  * **Blender**: Install via [Steam](https://store.steampowered.com/app/365670/Blender/) or the [official website](https://www.blender.org/download/).
  * **Redis**: You will need `redis-server.exe` or `memurai.exe` running.

> 🛑 **TERMINAL RULE:** If you don't see `(venv)` at the start of your line in the terminal, you must type `cmd` and press **Enter** before activating the environment\!

-----

### PART 1: FIRST-TIME SETUP (DO THIS ONLY ONCE)

#### 1\. Configure Environment Variables (`.env`) & Get API Key

The AI needs an API key to work. This key is stored in a special hidden file.

**Step A: Get your personal Groq API Key**

1.  Go to [console.groq.com](https://console.groq.com) and log in (using Google or GitHub is the fastest way).
2.  Look at the top right corner of the screen and click on the three horizontal lines (hamburger menu).
3.  From the menu, select **API Keys**.
4.  In the top right corner of the new page, click the **Create API Key** button. Give it a name (e.g., "Sunrise Local").
5.  ⚠️ **CRITICAL:** Copy the key immediately\! (It usually starts with `gsk_...`). The system will only show it to you ONCE. If you close the pop-up without copying it, you will lose it forever. Save it somewhere safe.

**Step B: Create the `.env` file**

1.  In the root folder (`SUNRISE_PROJECT`), find the file named `.env.example`.
2.  Copy this file and rename the copy to exactly `.env` (ensure there is no `.example` or `.txt` at the end).
3.  Open this new `.env` file with VS Code or any text editor.
4.  Find the `LLM_API_KEY=` line and paste your copied key right after the `=` sign (no spaces).

Example of what your `.env` should look like:

```env
LLM_API_KEY=gsk_your_actual_long_key_here
```

#### 2\. Initialize Backend & Database

Open a **NEW** terminal. Type `cmd` and press **Enter**. Then run the following commands line by line:

```bat
:: 1. Create virtual environment
python -m venv venv

:: 2. Activate it
venv\Scripts\activate

:: 3. Install dependencies & fix conflicts
pip install -r requirements.txt

:: 4. Create Database and Test User
python create_db.py
python create_user.py
```

#### 3\. Initialize Frontend

Open a **NEW** terminal. Type `cmd` and press **Enter**. Then run:

```bat
cd frontend
npm install
```

-----

### PART 2: UPDATING

*(Do this ONLY when you pull new code from GitHub)*

**Step A: Update Backend**
Open a **NEW** terminal. Type `cmd` and press **Enter**.

```bat
venv\Scripts\activate
pip install -r requirements.txt
```

**Step B: Update Frontend**
Open a **NEW** terminal. Type `cmd` and press **Enter**.

```bat
cd frontend
npm install
```

-----

### PART 3: DAILY RUN

*(Do this EVERY TIME you want to use the app)*

**Order matters\!** You will need 3 separate terminals running simultaneously in VS Code, plus ensuring Redis is running.

#### Step 0: Start Redis

Depending on how you installed Redis, choose ONE option:

  * **Option A: Installed as an Application / Service (Memurai or MSI Installer)**
    Redis likely starts automatically in the background when you turn on your PC. You don't need to do anything. *(If Celery fails later, check Task Manager to see if the service is running).*
  * **Option B: Downloaded as a Folder (Portable Version)**
    Open File Explorer, navigate to that folder, and double-click `redis-server.exe`. **Keep that window open\!**
  * **Option C: Using Docker (Recommended if installed)**
    Open any terminal outside of VS Code and run:
    ```bat
    docker run -p 6379:6379 -d redis
    ```

#### Terminal \#1: Backend Server (Flask)

Open a **NEW** terminal. Type `cmd` and press **Enter**.

```bat
venv\Scripts\activate
python run.py
```

> ✅ **Success:** Should say `* Running on http://127.0.0.1:5000`.

#### Terminal \#2: Worker (Celery)

Open a **NEW** terminal. Type `cmd` and press **Enter**.

```bat
venv\Scripts\activate
celery -A worker.celery worker --loglevel=info --pool=solo
```

> ✅ **Success:** Should show the Celery logo and `[INFO/MainProcess] celery@... ready`.

#### Terminal \#3: Frontend (Next.js)

Open a **NEW** terminal. Type `cmd` and press **Enter**.

```bat
cd frontend
npm run dev
```

> ✅ **Success:** Should say `✓ Ready in ...ms` and `http://localhost:3000`.

-----

### Final Step: Testing

1.  Go to [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000) in your browser.
2.  Type a prompt (e.g., "A wooden table") and click **Generate**.
3.  Check **Terminal \#2 (Celery)**: you should see Blender starting.

-----

### Troubleshooting

  * **Terminal errors:** If activation fails, always make sure you typed `cmd` first.
  * **CORS Error:** Make sure `BASE_URL` in `frontend/services/api.ts` matches your browser address (`localhost` or `127.0.0.1`).
  * **Wrong Folder Error:** If a command says "file not found" or similar, make sure you opened a new terminal so it starts in the project's root folder.
  * **Redis/Celery Error:** If Terminal \#2 says "Connection Error" or "Consumer: Cannot connect", your Redis server is not running. Revisit Phase 3, Step 0.

