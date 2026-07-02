# Kayfa Sales Agent 

An AI-powered sales agent for [Kayfa](https://kayfa.io/) — a leading Arabic e-learning platform. Built with Streamlit, OpenAI GPT-4o-mini, LangChain, ChromaDB, and MongoDB.

## Architecture Overview

```
kayfa-sales-agent/
├── app/
│   ├── Home.py                  # Streamlit entrypoint (auth gate)
│   ├── pages/
│   │   ├── 1_Chat_Agent.py      # Part 1 — Visitor chat (sales agent)
│   │   ├── 2_CRM_Tickets.py     # Part 1 — Admin lead management
│   │   ├── 3_Cost_Monitor.py    # Part 2.A — Admin cost tracking
│   │   └── 4_Behaviour_Trace.py # Part 2.B — Admin decision tracing
├── core/
│   ├── auth.py                  # Signup/login, session, role checks
│   ├── db.py                    # MongoDB client + collection getters
│   └── config.py                # Env vars, provider-agnostic pricing table
├── rag/
│   ├── ingest.py                # Load + chunk + embed data/
│   ├── retriever.py             # search_kb() — semantic search over KB
│   └── vectorstore/             # Local ChromaDB cache (gitignored)
├── agent/
│   ├── tools.py                 # search_kb, get_roadmap, create_lead_ticket
│   ├── prompts.py               # System prompt (bilingual EN/AR)
│   ├── graph.py                 # ReAct loop — tool-calling orchestration
│   └── usage_logger.py          # Writes usage_logs + behaviour_logs
├── data/                          # Kayfa knowledge base
│   ├── json/
│   │   ├── kayfa_courses.json   # 52 courses catalog
│   │   └── kayfa_roadmaps.json  # 13 learning paths
│   └── text/                    # Markdown docs (company, policies, diplomas)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- MongoDB instance (local or [MongoDB Atlas](https://www.mongodb.com/atlas))
- OpenAI API key

### 2. Clone & Setup

```bash
git clone <repo-url>
cd kayfa-sales-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys:
# OPENAI_API_KEY=sk-your-key
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
# MONGODB_DB_NAME=kayfa_sales_agent
```

### 4. Build Knowledge Base

```bash
python rag/ingest.py
```

This embeds all courses, roadmaps, and markdown documents into ChromaDB.

### 5. Run the App

```bash
cd app
streamlit run Home.py
```

The app will open at `http://localhost:8501`.

### 6. First Login

- Sign up as a new user (default role: `visitor`)
- To create an admin user, manually update the role in MongoDB:
  ```javascript
  db.users.updateOne({username: "youruser"}, {$set: {role: "admin"}})
  ```

## Project Structure Rationale

| Directory | Purpose |
|-----------|---------|
| `core/` | Infrastructure used by all parts — DB, auth, config |
| `rag/` | Knowledge layer — ingestion, embedding, retrieval |
| `agent/` | Reasoning layer — tools, prompts, orchestration, logging |
| `app/` | Streamlit UI — entrypoint and pages |
| `data/` | Source knowledge base (regenerable, not committed as embeddings) |
| `tests/` | Unit, integration, and E2E tests |

This separation lets **Part 2** (monitoring) read `usage_logs` independently without importing agent internals.

## Key Design Decisions

### Provider-Agnostic Cost Monitor
The pricing table in `core/config.py` is keyed by `(provider, model)` tuples. Adding Claude or Gemini later only requires adding entries — no rearchitecture.

### Bilingual Support (EN/AR)
The system prompt instructs the agent to respond in the user's language. Arabic dialect handling is supported via GPT-4o-mini's native multilingual capabilities.

### Idempotent Ingestion
Running `python rag/ingest.py` rebuilds the vector store from scratch. Embeddings are regenerable and gitignored.

### Security
- Passwords hashed with bcrypt
- `.env` never committed (`.env.example` documents required vars)
- Admin pages protected by role checks (not just UI hiding)
- API keys validated at startup with clear error messages

## Docker

```bash
docker build -t kayfa-sales-agent .
docker run -p 8501:8501 --env-file .env kayfa-sales-agent
```

## Running Tests

```bash
pytest tests/ -v --cov=.
```

## License

Private — for Kayfa Digital Solutions internal use.
