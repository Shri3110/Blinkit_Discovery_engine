# Railway Deployment Plan

This document outlines the steps required to deploy the AI Discovery Engine (both the FastAPI backend and the React/Vite frontend) to [Railway](https://railway.app/).

## Prerequisites
- A GitHub repository containing this project.
- A Railway account connected to your GitHub account.

## 1. Application Adjustments Needed Before Deployment

### A. Environment Variables & API URLs
Currently, the frontend hardcodes `http://localhost:8000` for backend API calls. 
1. **Frontend**: Update the API calls in `App.jsx` to use an environment variable (e.g., `import.meta.env.VITE_API_URL`) so it can dynamically point to the deployed backend URL.
2. **Backend**: Ensure that `GROQ_API_KEY` is not hardcoded but loaded from the environment (already implemented).
3. **CORS**: Update `allow_origins` in `main.py` from `["*"]` to include the specific deployed frontend URL for security, or leave it as `["*"]` for initial testing.

### B. Persistent Storage (Databases)
The backend uses ChromaDB and a SQLite database. On a platform like Railway, the filesystem is ephemeral. If the app restarts, local databases will be wiped.
1. Update database paths (ChromaDB and SQLite) to point to a specific directory (e.g., `/data`).
2. On Railway, you will need to provision a **Volume** and attach it to the `/data` mount path for your backend service so data persists across deployments.

### C. Requirements File
Ensure you have a `requirements.txt` in the root directory for the backend, listing dependencies such as `fastapi`, `uvicorn`, `chromadb`, `groq`, `sqlalchemy`, etc.

---

## 2. Deploying the Backend (FastAPI)

1. **Create a New Project** on Railway and select "Deploy from GitHub repo".
2. Select the repository containing this codebase.
3. Railway will attempt to automatically build using Nixpacks.
4. **Configure the Service**:
   - Go to the service settings.
   - Set the **Root Directory** to `/` (the root of the repo).
   - Set the **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables**:
   - Go to the Variables tab.
   - Add `GROQ_API_KEY` with your actual Groq API key.
6. **Add a Persistent Volume**:
   - Go to the Volumes tab.
   - Create a new volume and mount it to `/data`.
   - Ensure your code has been updated to use `/data` for its SQLite and ChromaDB paths.
7. **Generate a Public Domain**:
   - Go to the Settings tab -> Networking.
   - Click "Generate Domain" to get a public URL (e.g., `ai-discovery-backend-production.up.railway.app`).

---

## 3. Deploying the Frontend (React / Vite)

1. In the same Railway project, click **New** -> **GitHub Repo**.
2. Select the same repository again to create a second service.
3. **Configure the Service**:
   - Go to settings.
   - Set the **Root Directory** to `/frontend`.
   - Railway will automatically detect the Vite React app and configure the build command (`npm run build`).
4. **Add Environment Variables**:
   - Add `VITE_API_URL` and set it to the public domain you generated for the backend (e.g., `https://ai-discovery-backend-production.up.railway.app`).
5. **Generate a Public Domain**:
   - Go to the Settings tab -> Networking.
   - Click "Generate Domain" to get a public URL for your frontend.

---

## 4. Post-Deployment Verification
- Visit the frontend URL.
- Ensure the network tab shows successful API requests to the backend URL rather than `localhost:8000`.
- Generate an insight and verify that the Groq LLM responds successfully.
