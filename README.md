# Uproad AI — Fleet Dispatch

AI-powered roadside assistance dispatch for commercial fleets. Drivers text or call in problems, the AI agent creates a job and dispatches vendors via SMS and voice call.

## How It Works

1. **Driver texts** the Twilio number → AI creates job + dispatches vendor
2. **Driver calls** the Twilio number → ElevenLabs voice agent gathers info → AI dispatches vendor
3. **AI calls vendor** using an ElevenLabs voice agent (sounds human) to confirm dispatch
4. **Dashboard** shows all jobs, status, agent activity

---

## Deploy to Railway (5 minutes)

### Step 1 — Push to GitHub

```bash
cd uproad-app
git init
git add .
git commit -m "Initial commit"
# Create a new repo at github.com then:
git remote add origin https://github.com/YOUR_USERNAME/uproad-ai.git
git push -u origin main
```

### Step 2 — Create Railway Project

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your repo
3. Railway will auto-detect the `railway.toml` and start building

### Step 3 — Set Environment Variables

In Railway dashboard → your service → Variables, add:

```
ANTHROPIC_API_KEY=sk-ant-...
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
ELEVENLABS_API_KEY=sk_...
BASE_URL=https://YOUR-APP.up.railway.app
SECRET_KEY=generate-a-random-string-here
```

**Important:** Set `BASE_URL` to the Railway URL Railway assigns (shown in the service settings).

### Step 4 — Configure Twilio Webhooks

In [Twilio Console](https://console.twilio.com) → Phone Numbers → your number (+1 914 730 5995):

- **A message comes in (SMS):** `https://YOUR-APP.up.railway.app/webhook/sms/inbound` (HTTP POST)
- **A call comes in (Voice):** `https://YOUR-APP.up.railway.app/webhook/voice/inbound` (HTTP POST)

### Step 5 — Test It

Text `+1 914 730 5995` with a problem like:
> "Blown tire on I-95 mile marker 42, truck unit 447, need help ASAP"

Watch the dashboard at `https://YOUR-APP.up.railway.app` — a job should appear within seconds and the agent will start dispatching.

---

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env   # fill in your keys
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # runs on :5173 with proxy to :8000
```

---

## Architecture

```
Driver SMS/Call
      │
   Twilio (+19147305995)
      │
   FastAPI (Railway)
      ├── /webhook/sms/inbound  → creates Job → runs Claude agent
      ├── /webhook/voice/inbound → TwiML → WebSocket proxy → ElevenLabs intake agent
      └── /ws/voice/*           → bidirectional audio proxy (ulaw_8000 ↔ ElevenLabs)
             │
         Claude claude-3-5-sonnet (agentic loop)
             ├── find_vendors(problem)
             ├── send_sms(vendor_phone, message)
             ├── make_voice_call(vendor_phone)  → ElevenLabs dispatch agent
             └── update_job(status, vendor, eta)

React Dashboard (served from FastAPI /dist)
  ├── Dashboard — stats + active jobs
  ├── All Jobs — full job table
  ├── Job Detail — actions + agent log
  └── New Job — manual job creation
```

## Stack

- **Backend:** FastAPI + SQLite + SQLAlchemy
- **AI Agent:** Anthropic Claude claude-3-5-sonnet-20241022 (tool calling loop)
- **Telephony:** Twilio (SMS + Voice / Media Streams)
- **Voice AI:** ElevenLabs Conversational AI (WebSocket, Charlie voice)
- **Frontend:** React + Vite + Tailwind CSS
- **Deploy:** Railway (single service)
