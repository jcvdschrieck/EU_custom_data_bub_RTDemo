# EU Custom Data Hub — Real-Time Demo

A real-time simulation of the European Commission's **Taxation and Customs Union** transaction monitoring system.  
The application streams B2C cross-border e-commerce transactions across 7 EU member states, detects VAT rate anomalies, and routes suspicious cases to an AI agent that produces a compliance verdict with legislation references.

---

## Architecture overview

```
┌─────────────────────────────────────────────┐
│  FastAPI backend (port 8505)                │
│  ├─ Simulation engine  — replays March 2026 │
│  ├─ Alarm checker      — VAT ratio monitor  │
│  ├─ Agent worker       — Claude AI analysis │
│  └─ SSE stream         — live queue push    │
└────────────────┬────────────────────────────┘
                 │ HTTP / SSE
┌────────────────▼────────────────────────────┐
│  React + Vite frontend (port 5175)          │
│  ├─ Main        — live transaction stream   │
│  ├─ Dashboard   — VAT metrics & charts      │
│  ├─ Suspicious  — flagged transactions      │
│  └─ Agent Log   — AI analysis console       │
└─────────────────────────────────────────────┘
                 │ static mount
┌────────────────▼────────────────────────────┐
│  Ireland Revenue app  /ireland-app/          │
│  Standalone HTML — investigation queue      │
└─────────────────────────────────────────────┘
                 │ subprocess
┌────────────────▼────────────────────────────┐
│  vat_fraud_detection/ (git submodule)       │
│  Claude-powered VAT compliance analyser     │
│  with RAG over EU VAT legislation           │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11 + |
| Node.js | 18 + |
| npm | 9 + |

---

## Setup

### 1. Clone with submodule

```bash
git clone --recurse-submodules https://github.com/jcvdschrieck/EU_custom_data_hub_RTDemo.git
cd EU_custom_data_hub_RTDemo
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

### 3. AI agent API key

The VAT fraud detection agent calls the **Anthropic Claude API**. Copy the example env file and add your key:

```bash
cp vat_fraud_detection/.env.example vat_fraud_detection/.env
# then edit vat_fraud_detection/.env and set ANTHROPIC_API_KEY=sk-ant-...
```

> Without a key the agent will still run — suspicious transactions will receive an `uncertain` verdict instead of an AI-powered compliance analysis.

### 4. Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Seed the databases

```bash
python seed_databases.py
```

This creates two SQLite databases in `data/`:
- `european_custom.db` — ~9 000 historical transactions (Feb 2026)
- `simulation.db`      — ~1 500 March 2026 transactions ready to be replayed

---

## Running

Open two terminals:

**Terminal 1 — API**
```bash
uvicorn api:app --port 8505 --reload
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

Then open [http://localhost:5175](http://localhost:5175).

Use the **▶ Play** button in the header to start the simulation.

---

## Application pages

| Page | URL | Description |
|------|-----|-------------|
| Main | `/` | Live transaction stream (SSE), KPI tiles, active alarms |
| Dashboard | `/dashboard` | VAT metrics, charts by country & category |
| Suspicious | `/suspicious` | Transactions flagged by the alarm system |
| Agent Log | `/agent-log` | Console view of AI analysis events with legislation references |
| Ireland Queue | `http://localhost:8505/ireland-app/` | Irish Revenue investigation app (separate design) |

---

## Simulation scenario

The simulation replays **March 2026** at configurable speed (default: 2 sim-hours / real-second → full month in ~6 minutes).

A fraud scenario is embedded:
- **Supplier**: TechZone GmbH (Germany) — sells electronics B2C to Irish consumers
- **Fraud**: applies 0% VAT (food/zero-rated rate) instead of the correct 23% Irish standard rate
- **Detection**: the alarm engine detects the VAT/value ratio deviation during week 2 of March
- **Investigation**: flagged transactions are analysed by the Claude agent and forwarded to the Ireland Revenue queue with full legislation references

---

## Project structure

```
EU_custom_data_hub_RTDemo/
├── api.py                    # FastAPI app — all endpoints + SSE stream
├── seed_databases.py         # One-time DB seeder
├── requirements.txt
├── lib/
│   ├── config.py             # Ports, paths, simulation time window
│   ├── catalog.py            # Suppliers, countries, VAT rates
│   ├── database.py           # SQLite helpers
│   ├── seeder.py             # Historical + simulation data generator
│   ├── simulator.py          # Async simulation loop
│   ├── alarm_checker.py      # VAT ratio deviation alarm engine
│   └── agent_bridge.py       # Subprocess bridge → vat_fraud_detection
├── frontend/                 # React + Vite (port 5175)
│   └── src/
│       ├── pages/            # Main, Dashboard, Suspicious, Agent Log
│       └── components/       # EclLayout, SimulationWidget, charts
├── ireland_app/
│   └── index.html            # Standalone Irish Revenue investigation app
├── vat_fraud_detection/      # Git submodule — Claude VAT compliance agent
│   ├── _analyse_tx.py        # Subprocess entry point (called by agent_bridge)
│   ├── lib/analyser.py       # Core AI analysis engine
│   ├── data/chroma_db/       # RAG vector store (EU VAT legislation)
│   └── prompts/              # LLM system prompts
└── data/                     # SQLite databases (git-ignored, created by seeder)
```

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/queue` | Latest 30 transactions (REST snapshot) |
| GET | `/api/queue/stream` | SSE stream — one transaction per event |
| GET | `/api/transactions` | Paginated historical query |
| GET | `/api/metrics` | VAT aggregates with filters |
| GET | `/api/alarms` | Alarm list |
| GET | `/api/suspicious` | Last 50 suspicious transactions |
| GET | `/api/agent-log` | AI analysis history with legislation refs |
| GET | `/api/agent-processing` | Transactions currently being analysed |
| GET | `/api/ireland-queue` | Cases forwarded to Ireland investigation |
| GET | `/api/ireland-case/{id}` | Full case detail |
| POST | `/api/simulation/start` | Start simulation |
| POST | `/api/simulation/pause` | Pause |
| POST | `/api/simulation/resume` | Resume |
| POST | `/api/simulation/speed` | Set speed `{"speed": <float>}` |
| POST | `/api/simulation/reset` | Reset to start |

---

## License

Demo project — European Commission Taxation and Customs Union simulation.
