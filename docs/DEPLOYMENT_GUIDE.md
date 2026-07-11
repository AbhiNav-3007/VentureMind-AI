# Deploying VentureMind AI for Free (Render & Vercel)

This guide walks you through deploying the VentureMind AI application using a **100% free hybrid hosting model** (no credit card required):
1. **Database:** Hosted on **Supabase** (Lifetime Free PostgreSQL).
2. **Backend (FastAPI):** Hosted on **Render** (Free Web Service via Docker).
3. **Frontend (React):** Hosted on **Vercel** (Free Vite/React deployment).
4. **AI & Storage Services:** Hosted on **IBM Cloud Lite** plans (watsonx.ai and Cloud Object Storage).

---

## Prerequisites

Before starting, ensure you have:
- A **GitHub account** with your VentureMind AI codebase pushed to a repository.
- An **IBM Cloud Account** (your active Trial/Lite plan for watsonx.ai keys).
- A free account on **[Supabase](https://supabase.com/)** and **[Render](https://render.com/)**.
- A free account on **[Vercel](https://vercel.com/)**.

---

## STEP 1 — Create a Free Database on Supabase

1. Log in to **[Supabase](https://supabase.com/)**.
2. Click **New Project** and select your organization.
3. Choose a project name (e.g., `VentureMind-DB`), set a secure database password, and select a region closest to your users.
4. Click **Create new project** and wait for the database to provision (takes about 1 minute).
5. Once ready, go to **Project Settings** (gear icon in the sidebar) → **Database**.
6. Scroll down to the **Connection string** section and click on the **URI** tab.
7. Copy the connection string. It will look like this:
   ```
   postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
8. Replace `[YOUR-PASSWORD]` with your actual database password.
9. Convert the protocol from `postgresql://` to `postgresql+asyncpg://` so that the FastAPI async driver functions correctly:
   ```
   postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:your_password@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
10. Save this database connection string. We will set it as the `DATABASE_URL` environment variable on Render.

---

## STEP 2 — Deploy the FastAPI Backend on Render

Render runs containerized applications directly from your GitHub repository using Docker.

1. Log in to **[Render.com](https://render.com/)** (sign in using your GitHub account for easy access).
2. Click **New +** in the top right corner and select **Web Service**.
3. Select **Connect repository** and choose your `VentureMind-AI` repository.
4. Configure the Web Service:
   - **Name:** `venturemind-backend`
   - **Region:** Select a location closest to you (e.g., Singapore or Oregon).
   - **Branch:** `main`
   - **Root Directory:** `backend` *(Crucial: this tells Render to focus on the backend folder)*
   - **Runtime:** `Docker` *(Render will automatically detect the Dockerfile inside backend/)*
5. Scroll down to the **Instance Type** section and verify that the **Free** tier is selected.
6. Click **Advanced** and add the following **Environment Variables**:
   - `DATABASE_URL` — *(Your converted Supabase connection string from Step 1)*
   - `IBM_WATSONX_URL` — `https://us-south.ml.cloud.ibm.com`
   - `IBM_WATSONX_API_KEY` — *(Your watsonx.ai API Key)*
   - `IBM_WATSONX_PROJECT_ID` — *(Your watsonx.ai Project ID)*
   - `IBM_GRANITE_MODEL_ID` — `ibm/granite-3-8b-instruct` *(Recommended Granite-3 model)*
   - `IBM_COS_API_KEY` — *(Your Cloud Object Storage API Key)*
   - `IBM_COS_BUCKET_NAME` — *(Your COS Bucket Name)*
7. Click **Deploy Web Service**.
8. Render will build your Docker container. Once the build completes and states *Live*, copy your backend URL from the top of the page (e.g., `https://venturemind-backend.onrender.com`).

---

## STEP 3 — Deploy the React Frontend on Vercel

Vercel is the premier platform for hosting static Vite/React applications.

1. Log in to **[Vercel.com](https://vercel.com/)** using your GitHub account.
2. Click **Add New** → **Project**.
3. Import your `VentureMind-AI` repository.
4. Configure the Project:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click *Edit* and select the `frontend` folder.
5. Expand the **Environment Variables** section and add:
   - **Name:** `VITE_API_URL`
   - **Value:** Your Render backend URL (e.g., `https://venturemind-backend.onrender.com` — *without a trailing slash*).
   - **Name:** `VITE_WS_URL`
   - **Value:** Your Render backend URL but starting with `wss://` instead of `https://` (e.g., `wss://venturemind-backend.onrender.com`).
6. Click **Deploy**.
7. Vercel will build your static files and deploy them. Once complete, it will provide your live website link (e.g., `https://venturemind-ai.vercel.app`)!
