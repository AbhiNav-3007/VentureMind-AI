# Deploying VentureMind AI for Free

This guide walks you through deploying the VentureMind AI application using a **hybrid free hosting model**:
1. **Database:** Hosted on **Neon.tech** (100% Free PostgreSQL).
2. **Backend (FastAPI) & Frontend (React/Nginx):** Hosted on **IBM Cloud Code Engine** (serverless container hosting covered by your IBM Cloud Trial/Lite quotas).
3. **AI & Storage Services:** Hosted on **IBM watsonx.ai, Watson Discovery, and Cloud Object Storage (COS)** (using IBM Cloud Lite plan tiers).

---

## Prerequisites

Before starting, ensure you have:
- A **GitHub account** with your VentureMind AI codebase pushed to a private or public repository.
- An **IBM Cloud Account** (your active Trial plan).
- A free account on **[Neon.tech](https://neon.tech/)** or **[Supabase](https://supabase.com/)**.

---

## STEP 1 — Create a Free PostgreSQL Database

Since IBM Cloud does not offer a free tier for PostgreSQL, we will use **Neon** (or Supabase).

1. Log in to **[Neon.tech](https://neon.tech/)**.
2. Click **Create a Project**.
3. Name your project (e.g., `venturemind-db`) and select a region closest to you.
4. Once created, copy the **Connection String** from the dashboard.
5. Convert the protocol:
   - Your copied URL might look like: `postgresql://user:password@ep-xxxx.neon.tech/neondb`
   - You **MUST** change `postgresql://` to `postgresql+asyncpg://` so that the FastAPI async database driver works:
     ```
     postgresql+asyncpg://user:password@ep-xxxx.neon.tech/neondb?sslmode=require
     ```
   - Keep this URL safe; we will use it as your `DATABASE_URL` environment variable.

---

## STEP 2 — Deploy the FastAPI Backend on IBM Cloud Code Engine

**IBM Cloud Code Engine** runs containerized applications directly from your GitHub repository.

1. Go to the **[IBM Cloud Console](https://cloud.ibm.com/)**.
2. Search the catalog for **Code Engine** and click on it.
3. Click **Projects** in the left menu and click **Create**.
   - Name your project (e.g., `venturemind-project`).
   - Select your location (e.g., `Dallas` or `Frankfurt`).
   - Click **Create**.
4. Once the project status shows as *Active*, click on it to open the dashboard.
5. Select **Applications** in the left menu and click **Create**.
6. Set the configuration details:
   - **Name:** `venturemind-backend`
   - **Choose how to run your code:** Select **Source code**.
   - **Code repo URL:** Enter your GitHub repository URL (e.g., `https://github.com/your-username/venturemind-ai`).
   - *Note: If your repository is private, you will need to create and select a SSH/Git access token.*
   - Click **Specify build details**:
     - **Branch name:** `main`
     - **Context directory:** `backend/` (Crucial: this points Code Engine to the Python app).
     - **Dockerfile:** `Dockerfile`
     - Click **Next** → **Finish**.
7. Under **Runtime settings**:
   - Set **Listening port:** `8000`
   - Set resources: **0.25 vCPU / 0.5 GB memory** (this keeps resource usage minimal and free).
8. Under **Environment variables (optional)**, click **Add** to specify your configuration keys from your local `.env`:
   - `DATABASE_URL` (your Neon connection string from Step 1)
   - `IBM_WATSONX_URL`
   - `IBM_WATSONX_API_KEY`
   - `IBM_WATSONX_PROJECT_ID`
   - `IBM_GRANITE_MODEL_ID`
   - `IBM_DISCOVERY_API_KEY`
   - `IBM_DISCOVERY_URL`
   - `IBM_COS_API_KEY`
   - `IBM_COS_BUCKET_NAME`
9. Click **Create** to launch the build.
10. Once the build finishes, copy the **Application URL** generated at the top (e.g., `https://venturemind-backend.xxxx.codeengine.appdomain.cloud`). This is your live backend endpoint!

---

## STEP 3 — Connect and Deploy the Frontend

Now that your backend is running, we need to tell the frontend React client where to send API requests.

### 1. Update the Frontend Config
In your local workspace:
- Open [`frontend/src/services/api.ts`](file:///d:/STUDY%20MATERIAL/Internship/IBM%20skillbuild%20internship/IBM%20BOB%20INTERNSHIP%20PROJECT/venturemind-ai/frontend/src/services/api.ts) or your `.env` configuration.
- Update the base URL pointing to the Code Engine backend URL you copied in the previous step.
- Save, commit, and push this change to your GitHub repository.

### 2. Deploy Frontend to Code Engine
1. Return to your **Code Engine Project** in the IBM Cloud Console.
2. Select **Applications** and click **Create**.
3. Set the configuration details:
   - **Name:** `venturemind-frontend`
   - **Choose how to run your code:** Select **Source code**.
   - **Code repo URL:** Enter your GitHub repository URL.
   - Click **Specify build details**:
     - **Branch name:** `main`
     - **Context directory:** `frontend/` (Crucial: this points Code Engine to the React app).
     - **Dockerfile:** `Dockerfile`
     - Click **Next** → **Finish**.
4. Under **Runtime settings**:
   - Set **Listening port:** `80` (or the port defined in your `frontend/Dockerfile` Nginx configuration).
   - Set resources: **0.25 vCPU / 0.5 GB memory**.
5. Click **Create**.
6. Once the build completes, open the provided frontend URL in your browser.

**Your VentureMind AI application is now fully deployed and running live on the cloud, 100% free!** 🎉
