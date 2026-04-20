Local Setup & Execution Guide: SUNRISE Project

This guide explains how to configure and run the End-to-End generation pipeline locally.
Requirements (Before you start)
Python (3.10+): IMPORTANT: During installation, you must check the box "Add Python.exe to PATH".
Node.js (v20+): Required for the frontend.
Blender: Install via Steam or the official website.
Redis: You will need redis-server.exe or memurai.exe running.
TERMINAL RULE: If you don't see (venv) at the start of your line, you must type cmd and press Enter before activating the environment!

PART 1: FIRST-TIME SETUP (DO THIS ONLY ONCE)
1. Configure Environment Variables (.env) & Get API Key
The AI needs an API key to work. This key is stored in a special hidden file.
Step A: Get your personal Groq API Key
Go to console.groq.com and log in (using Google or GitHub is the fastest way).
Look at the top right corner of the screen and click on the three horizontal lines (hamburger menu).
From the menu, select API Keys.
In the top right corner of the new page, click the Create API Key button. Give it a name (e.g., "Sunrise Local").
CRITICAL: Copy the key immediately! (It usually starts with gsk_...). The system will only show it to you ONCE. If you close the pop-up without copying it, you will lose it forever and will have to generate a new one. Save it somewhere safe.
Step B: Create the .env file from the example
In the root folder (SUNRISE_PROJECT), find the file named .env.example.
Copy this file and rename the copy to exactly .env (ensure there is no .example or .txt at the end).
Open this new .env file with VS Code or whatever text editor you use.
Find the LLM_API_KEY= line and paste your copied key right after the = sign (no spaces). It should look something like this:

E.g. code you need to have in .env:
LLM_API_KEY=gsk_your_actual_long_key_here
2. Initialize Backend & Database
Open a NEW terminal.
Type cmd and press Enter.
Then run:
Write in the terminal:
:: 1. Create virtual environment
python -m venv venv

:: 2. Activate it
venv\Scripts\activate

:: 3. Install dependencies & fix conflicts
pip install -r requirements.txt

:: 4. Create Database and Test User
python create_db.py
python create_user.py
3. Initialize Frontend
Open a NEW terminal.
Type cmd and press Enter.  
Write in the terminal:
cd frontend
npm install

PART 2: UPDATING (DO THIS ONLY WHEN DOWNLOADING NEW CODE)
Do this ONLY when you pull updates from GitHub.
Step A: Update Backend
Open a NEW terminal.
Type cmd and press Enter. 
Activate: venv\Scripts\activate (skip if you already see (venv)):
Write in the terminal:
pip install -r requirements.txt
Step B: Update Frontend
Open a NEW terminal.
Type cmd and press Enter. 
Write in the terminal:
cd frontend
npm install

PART 3: DAILY RUN (DO THIS EVERY TIME YOU WANT TO USE THE APP)
Order matters! You will need 3 separate terminals running simultaneously in VS Code or whatever you use, plus ensuring Redis is running.
Step 0: Start Redis
Depending on how you installed Redis on your system, choose ONE of the following options:
Option A: Installed as an Application / Service (Memurai or MSI Installer)

If you installed it using a standard setup wizard, Redis likely starts automatically in the background when you turn on your PC. You don't need to do anything. (If Celery fails later, check Task Manager to see if the service is running).
Option B: Downloaded as a Folder (Portable Version)

If you downloaded a zip file with Redis files, open File Explorer, navigate to that folder, and double-click redis-server.exe. Keep that window open!
Option C: Using Docker (Recommended if installed)

If you have Docker Desktop installed, simply open any terminal outside of VS Code and run:
Write in the terminal:
docker run -p 6379:6379 -d redis
Terminal #1: Backend Server (Flask)
Open a NEW terminal.
Type cmd and press Enter. 
Activate: venv\Scripts\activate (skip if you already see (venv)).
Write in the terminal:
python run.py
Success: Should say * Running on http://127.0.0.1:5000.
Terminal #2: Worker (Celery)
Open a NEW terminal.
Type cmd and press Enter. 
Activate: venv\Scripts\activate (skip if you already see (venv)).
Write in the terminal:
 celery -A worker.celery worker --loglevel=info --pool=solo
Success: Should show the Celery logo and [INFO/MainProcess] celery@... ready.
Terminal #3: Frontend (Next.js)
Open a NEW terminal.
Type cmd and press Enter. 
Run:
Write in the terminal:
cd frontend
npm run dev

Success: Should say ✓ Ready in ...ms and http://localhost:3000.

Final Step: Testing
Go to http://localhost:3000.
Type a prompt (e.g., "A wooden table") and click Generate.
Check Terminal #2 (Celery): you should see Blender starting.
Troubleshooting:
Terminal errors: If activation fails, always make sure you typed cmd first.
CORS Error: Make sure BASE_URL in frontend/services/api.ts matches your browser address (localhost or 127.0.0.1).
Wrong Folder Error: If a command says "file not found" or similar, make sure you opened a new terminal so it starts in the project's root folder.
Redis/Celery Error: If Terminal #2 says "Connection Error" or "Consumer: Cannot connect", your Redis server is not running. Revisit Phase 3, Step 0.
