\# 🌅 SUNRISE Project



AI-powered platform for generating and interacting with 3D assets using natural language.



\---



\## 📌 Overview



SUNRISE is a web-based system that enables users to generate, preview, and refine 3D models from simple text prompts.



The platform integrates:

\- Large Language Models (LLMs) for understanding user intent

\- Blender (bpy) for procedural 3D generation

\- A modern web interface for interaction and visualization



\---



\## 🏗 Architecture



The system follows a modular, layered architecture:



User → Frontend → Backend → LLM → bpy Script → Blender → 3D Asset → Preview



\### Components:

\- \*\*Frontend\*\* → User interface, preview, interaction

\- \*\*Backend\*\* → Orchestration, API, processing

\- \*\*LLM Layer\*\* → Prompt interpretation \& code generation

\- \*\*Validation Layer\*\* → Safety and script correctness

\- \*\*Blender Engine\*\* → 3D asset generation

\- \*\*Storage (future)\*\* → History and reproducibility



\---



\## 📁 Project Structure





SUNRISE\_PROJECT/

├── app/ # Backend (Flask)

├── config.py

├── run.py

├── requirements.txt

│

├── frontend/ # Frontend (Next.js)

│ ├── app/

│ ├── components/

│ ├── services/

│ ├── state/

│ ├── types/

│ └── public/

│

├── README.md





\---



\## ⚙️ Tech Stack



\### 🔹 Frontend

\- Next.js (React)

\- TypeScript

\- Zustand (state management)

\- React Three Fiber (3D rendering)

\- Tailwind CSS (optional styling)



\### 🔹 Backend

\- Flask (Python)

\- REST API

\- LLM integration (Claude / Gemini planned)



\### 🔹 3D Engine

\- Blender (bpy Python API)

\- GLB / OBJ export



\---



\## 🚀 Features (MVP)



\- Input natural language prompt  

\- Generate 3D asset using AI  

\- Preview model in browser  

\- Rotate / zoom / inspect object  

\- Download generated model  



\---



\## 🔄 Generation Flow



1\. User submits prompt  

2\. Backend processes request  

3\. LLM generates bpy script  

4\. Script is validated  

5\. Blender executes script  

6\. Model is exported (.glb)  

7\. Frontend displays preview  

8\. User downloads asset  



\---



\## 📅 Current Status



\- Backend: Initial architecture ready ✅  

\- Frontend: UI shell and state system in progress 🚧  

\- 3D: Basic Blender pipeline planned ⚙️  

\- Integration: Scheduled for alpha phase  



\---



\## 🧪 MVP Goal



Deliver a working pipeline:





Text Prompt → 3D Model → Preview → Download





Focus:

\- Simple objects (cube, table, pallet)

\- Reliable execution

\- Clear UI feedback



\---



\## ▶️ Running the Project



\### 🔹 Frontend



```bash

cd frontend

npm install

npm run dev



Runs on:

👉 http://localhost:3000



🔹 Backend

pip install -r requirements.txt

python run.py



Runs on:

👉 http://localhost:5000

&#x20;(or configured port)



👥 Team Structure

Frontend Team → UI, state, preview, interaction

Backend Team → API, orchestration, LLM integration

3D Team → Blender scripts, asset generation

📌 Development Strategy



Phase 1 — MVP Pipeline



End-to-end generation flow



Phase 2 — Validation \& Safety



Script validation and error handling



Phase 3 — UI \& Preview



Interactive 3D viewer



Phase 4 — Refinement



Multi-step editing and iteration



Phase 5 — Storage \& History



Session tracking and versioning

⚠️ Notes

Frontend and backend are developed independently

Mock services are used before integration

Backend-first approach is recommended for stability

Alpha prototype will integrate full pipeline

🔮 Future Improvements

Image-based generation

Multi-input prompts

Improved geometry quality

Real-time updates (WebSockets)

Cloud deployment

📎 License



This project is for academic and research purposes.



✨ Acknowledgment



Developed as part of the SUNRISE project focusing on AI-driven 3D asset generation.

