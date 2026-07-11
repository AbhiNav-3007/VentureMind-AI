# IBM Cloud Setup & Connection Guide for VentureMind AI

## Overview

VentureMind AI uses 4 IBM Cloud services. This guide walks you through creating each service, getting credentials, and configuring your `.env` file — step by step.

---

## STEP 1 — Create an IBM Cloud Account

1. Go to [https://cloud.ibm.com/registration](https://cloud.ibm.com/registration)
2. Sign up for a **Lite (free) account** — no credit card required
3. Verify your email and log in

---

## STEP 2 — IBM watsonx.ai (IBM Granite LLM)

### Create the Service

1. Go to [https://dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Click **"Get started"** or navigate to IBM watsonx
3. On the watsonx homepage, click **"Launch"** under **Watson Studio**
4. If prompted, create a **Watson Studio** instance (Lite plan is free)

### Get Your API Key

1. Go to [https://cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)
2. Click **"Create an IBM Cloud API key"**
3. Name it `venturemind-key`
4. **Copy the API key immediately** — it won't be shown again
5. Paste it in your `.env` as:
   ```
   IBM_WATSONX_API_KEY=your_copied_key_here
   ```

### Get Your Project ID

1. Go to [https://dataplatform.cloud.ibm.com/projects](https://dataplatform.cloud.ibm.com/projects)
2. Create a new project: click **"New project"** → **"Create an empty project"**
3. Name it `VentureMind AI`
4. After creation, go to **Manage** tab
5. Copy the **Project ID** (alphanumeric string)
6. Paste in `.env` as:
   ```
   IBM_WATSONX_PROJECT_ID=your_project_id
   ```

### Configure the Endpoint

The default US-South endpoint is:
```
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Use Dallas region unless you created your instance in a different region:
- Dallas (US South): `https://us-south.ml.cloud.ibm.com`
- Frankfurt (EU): `https://eu-de.ml.cloud.ibm.com`
- Tokyo (AP): `https://jp-tok.ml.cloud.ibm.com`

### Select Your Granite Model

Available IBM Granite models on Lite plan:
- `ibm/granite-13b-instruct-v2` ← **recommended for this project**
- `ibm/granite-7b-lab`
- `ibm/granite-3-8b-instruct`

Set in `.env`:
```
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

### Test Connection

```bash
curl -X POST "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29" \
  -H "Authorization: Bearer $(curl -X POST 'https://iam.cloud.ibm.com/identity/token' \
    -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_API_KEY" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")" \
  -H "Content-Type: application/json" \
  -d '{"model_id":"ibm/granite-13b-instruct-v2","input":"Hello IBM Granite!","project_id":"YOUR_PROJECT_ID","parameters":{"max_new_tokens":50}}'
```

---

## STEP 3 — IBM Watson Discovery (RAG)

### Create the Service

1. Go to [https://cloud.ibm.com/catalog/services/watson-discovery](https://cloud.ibm.com/catalog/services/watson-discovery)
2. Select the **Lite plan** (free — 1000 documents, 1 collection)
3. Choose **Dallas** region
4. Click **Create**
5. Wait for provisioning (1–2 minutes)

### Get Credentials

1. Click on your Discovery instance from [https://cloud.ibm.com/resources](https://cloud.ibm.com/resources)
2. Go to **Service credentials** tab
3. Click **"New credential"** → **Add**
4. Click the arrow to expand and copy:
   - `apikey` → paste as `IBM_DISCOVERY_API_KEY`
   - `url` → paste as `IBM_DISCOVERY_URL`

Example `.env` entries:
```
IBM_DISCOVERY_API_KEY=your_discovery_api_key
IBM_DISCOVERY_URL=https://api.us-south.discovery.watson.cloud.ibm.com/instances/abc123
```

### Create a Project and Collection

1. Open Watson Discovery UI (click **"Launch Watson Discovery"**)
2. Click **"New project"**
3. Name it `VentureMind Knowledge Base`
4. Select **Document Retrieval**
5. Upload startup/policy documents OR use the default sample content
6. Go to **Manage collections** → note your **Collection ID**
7. Go to **Project settings** → note your **Project ID**

```
IBM_DISCOVERY_PROJECT_ID=your_project_id
IBM_DISCOVERY_COLLECTION_ID=your_collection_id
IBM_DISCOVERY_VERSION=2023-03-31
```

### Upload Knowledge Documents (Optional but Recommended)

Upload these to Watson Discovery for best RAG results:
- Startup India Policy PDF: [https://startupindia.gov.in](https://startupindia.gov.in)
- MSME Policy documents from [https://msme.gov.in](https://msme.gov.in)
- Any business plan templates

**Note:** Watson Discovery is **optional** for local testing. The RAG pipeline falls back to ChromaDB if Discovery is unavailable. Agents still work without it.

---

## STEP 4 — IBM Cloud Object Storage (PDF Storage)

### Create the Service

1. Go to [https://cloud.ibm.com/catalog/services/cloud-object-storage](https://cloud.ibm.com/catalog/services/cloud-object-storage)
2. Select **Lite plan** (free — 25 GB/month)
3. Click **Create**

### Create a Bucket

1. Click **"Create bucket"**
2. Choose **Quickly** → Standard
3. Name: `venturemind-reports`
4. Region: **us-south (Dallas)**
5. Note the endpoint: `https://s3.us-south.cloud-object-storage.appdomain.cloud`

### Get Credentials

1. On your COS instance page, click **Service credentials**
2. Click **"New credential"** → enable **HMAC** → Add
3. Expand the credential and find:
   - `apikey` → `IBM_COS_API_KEY`
   - `resource_instance_id` → `IBM_COS_INSTANCE_CRN`

```
IBM_COS_API_KEY=your_cos_api_key
IBM_COS_INSTANCE_CRN=crn:v1:bluemix:public:cloud-object-storage:global:...
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_BUCKET_NAME=venturemind-reports
IBM_COS_AUTH_ENDPOINT=https://iam.cloud.ibm.com/identity/token
```

**Note:** IBM COS is **optional**. If not configured, PDFs are streamed directly from the backend without cloud storage.

---

## STEP 5 — IBM Orchestrate (Optional Master Coordinator)

IBM Orchestrate is available on paid plans. For the Lite/free tier:

1. Go to [https://cloud.ibm.com/catalog/services/ibm-watsonx-orchestrate](https://cloud.ibm.com/catalog/services/ibm-watsonx-orchestrate)
2. If you have access, create an instance and note:
   - `IBM_ORCHESTRATE_URL`
   - `IBM_ORCHESTRATE_API_KEY`

**If you don't have Orchestrate:** Leave these empty in `.env`. The system uses LangGraph as the internal orchestrator, which fully replaces Orchestrate functionality for local development.

---

## STEP 6 — Local Infrastructure (PostgreSQL + ChromaDB)

### PostgreSQL

**Option A — Docker (recommended):**
```bash
docker run -d \
  --name venturemind-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=venturemind \
  -p 5432:5432 \
  postgres:15-alpine
```

**Option B — Local install:**
```bash
# macOS
brew install postgresql
createdb venturemind

# Ubuntu/Debian
sudo apt install postgresql
sudo -u postgres createdb venturemind
```

### ChromaDB (Vector Database for RAG)

```bash
docker run -d \
  --name venturemind-chroma \
  -p 8001:8000 \
  -e ANONYMIZED_TELEMETRY=false \
  chromadb/chroma:latest
```

### Seed the Knowledge Base

After ChromaDB is running:
```bash
cd venturemind-ai
python scripts/seed_knowledge_base.py
```
This adds 8 startup/legal/funding documents to ChromaDB for RAG.

---

## STEP 7 — Complete .env Configuration

Create `venturemind-ai/backend/.env` from the example:

```bash
cp venturemind-ai/backend/.env.example venturemind-ai/backend/.env
```

Fill in all values:

```env
# App
APP_NAME=VentureMind AI
DEBUG=false

# PostgreSQL (local Docker)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/venturemind

# ChromaDB (local Docker)
CHROMA_HOST=localhost
CHROMA_PORT=8001

# IBM watsonx.ai (REQUIRED)
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_WATSONX_API_KEY=<your_api_key>
IBM_WATSONX_PROJECT_ID=<your_project_id>
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2

# IBM Watson Discovery (OPTIONAL — RAG fallback to ChromaDB if empty)
IBM_DISCOVERY_API_KEY=<your_discovery_api_key>
IBM_DISCOVERY_URL=<your_discovery_url>
IBM_DISCOVERY_PROJECT_ID=<your_discovery_project_id>
IBM_DISCOVERY_COLLECTION_ID=<your_collection_id>
IBM_DISCOVERY_VERSION=2023-03-31

# IBM Cloud Object Storage (OPTIONAL — PDFs streamed directly if empty)
IBM_COS_API_KEY=<your_cos_api_key>
IBM_COS_INSTANCE_CRN=<your_crn>
IBM_COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
IBM_COS_BUCKET_NAME=venturemind-reports
IBM_COS_AUTH_ENDPOINT=https://iam.cloud.ibm.com/identity/token

# IBM Orchestrate (OPTIONAL)
IBM_ORCHESTRATE_URL=
IBM_ORCHESTRATE_API_KEY=
```

---

## STEP 8 — Run the Application

### Start Backend

```bash
cd venturemind-ai/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Start Frontend

```bash
cd venturemind-ai/frontend

npm install
npm run dev
```

Open: http://localhost:5173

---

## STEP 9 — Test the Full System

### Quick Test via API

```bash
# Submit a startup idea
curl -X POST http://localhost:8000/api/v1/startups/generate \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "An AI-powered waste management platform for smart cities",
    "industry": "CleanTech",
    "country": "India",
    "budget": "₹25 Lakhs – 1 Crore"
  }'

# Response:
# {"startup_id": "abc-123...", "status": "pending", "message": "..."}

# Poll status
curl http://localhost:8000/api/v1/startups/abc-123.../status

# Get blueprint when done
curl http://localhost:8000/api/v1/startups/abc-123.../blueprint

# Get agent reasoning timelines
curl http://localhost:8000/api/v1/startups/abc-123.../timelines
```

### Test via UI
1. Open http://localhost:5173
2. Click **"Generate My Blueprint"**
3. Enter: `"An AI-powered waste management platform for smart cities"`
4. Click **Generate Startup Blueprint**
5. Watch the Agent Execution Dashboard with live reasoning timelines
6. Click **View Blueprint** when complete
7. Click **Export PDF** to download

---

## Docker Compose (Full Stack — One Command)

```bash
cd venturemind-ai

# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your IBM credentials

# 2. Start everything
docker-compose up --build

# Services:
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# Docs:     http://localhost:8000/docs
```

---

## Minimum Configuration (Works Without IBM Discovery + COS)

If you only have IBM watsonx.ai credentials, the system still works:

| Service | Required? | Fallback |
|---------|-----------|---------|
| IBM watsonx.ai (Granite) | **YES — required** | No fallback |
| PostgreSQL | **YES — required** | No fallback |
| ChromaDB | **YES — required** | No fallback |
| Watson Discovery | Optional | Falls back to ChromaDB-only RAG |
| IBM Cloud Object Storage | Optional | PDFs streamed directly |
| IBM Orchestrate | Optional | LangGraph handles orchestration |

---

## Troubleshooting

### "IBM Granite API key invalid"
- Check that the API key is copied correctly (no extra spaces)
- Ensure the API key has `watson-machine-learning` service permissions
- IAM → API keys → Verify the key

### "watsonx model not found"
- Try `ibm/granite-7b-lab` as an alternative
- Check [https://dataplatform.cloud.ibm.com/docs/content/wsj/getting-started/models.html](models page)

### "PostgreSQL connection refused"
- Verify Docker container is running: `docker ps`
- Check the port: `docker logs venturemind-postgres`

### "ChromaDB connection failed"
- Start ChromaDB: `docker run -d -p 8001:8000 chromadb/chroma`
- Verify: `curl http://localhost:8001/api/v1/heartbeat`

### "Blueprint shows empty sections"
- This is normal when IBM Granite returns incomplete JSON
- The system uses safe_parse_json with fallbacks
- Check backend logs for more details: `uvicorn app.main:app --log-level debug`

---

## IBM Cloud Free Tier Limits

| Service | Free Limit |
|---------|-----------|
| watsonx.ai | 20 API calls/day (Lite) |
| Watson Discovery | 1,000 documents, 2,500 queries/month |
| Cloud Object Storage | 25 GB storage, 20 GB download/month |

For the internship demo, the free tier is sufficient for ~5–10 blueprint generations per day.
