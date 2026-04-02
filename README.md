# 🌅 SUNRISE Project

AI-powered platform for generating and interacting with 3D assets using natural language.

---

## 📌 Overview

SUNRISE is a web-based system that enables users to generate, preview, and refine 3D models from simple text prompts.

### The platform integrates:
- Large Language Models (LLMs) for understanding user intent
- Blender (bpy) for procedural 3D generation
- A modern web interface for interaction and visualization

---

## 🏗 Architecture


User → Frontend → Backend → LLM → bpy Script → Blender → 3D Asset → Preview


### Components
- **Frontend** — UI, preview, interaction  
- **Backend** — API, orchestration, processing  
- **LLM Layer** — prompt interpretation & code generation  
- **Validation Layer** — script safety & correctness  
- **Blender Engine** — 3D asset generation  
- **Storage (future)** — history & reproducibility  

---

## 📁 Project Structure


SUNRISE_PROJECT/
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


---

## ⚙️ Tech Stack

### Frontend
- Next.js (React + TypeScript)
- Zustand (state management)
- React Three Fiber (3D rendering)

### Backend
- Flask (Python)
- REST API
- LLM integration (planned)

### 3D Engine
- Blender (bpy API)
- GLB export

---

## 🚀 MVP Features

- Text → 3D model generation  
- Interactive 3D preview  
- Camera controls (rotate / zoom)  
- Download generated asset  

---

## 🔄 Generation Flow

1. User submits prompt  
2. Backend processes request  
3. LLM generates bpy script  
4. Script is validated  
5. Blender executes script  
6. Model exported (.glb)  
7. Frontend displays preview  
8. User downloads asset  

---

## 📅 Current Status

- Backend: Initial architecture ready ✅  
- Frontend: UI shell + state in progress 🚧  
- 3D: Pipeline planned ⚙️  
- Integration: Week 2 (alpha phase)  

---

## 🧪 MVP Goal


Text Prompt → 3D Model → Preview → Download


Focus:
- simple objects (cube, pallet, table)
- stable execution
- clear UI feedback

---

## ▶️ Run the Project

### Frontend

```bash
cd frontend
npm install
npm run dev

➡️ http://localhost:3000

Backend
pip install -r requirements.txt
python run.py

➡️ http://localhost:5000

👥 Team
Frontend Team — UI & preview
Backend Team — API & orchestration
3D Team — Blender & generation
⚠️ Notes
Frontend and backend developed independently
Mock services used before integration
Alpha prototype will include full pipeline
🔮 Future Work
Image-based generation
Multi-input prompts
Better geometry quality
Real-time updates
Cloud deployment
📎 License

Academic / research use.

✨ Project

Developed as part of the SUNRISE project — AI-driven 3D asset generation.
