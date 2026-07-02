# 💬 Kayfa Sales Agent

An advanced, bilingual AI-powered Sales Agent and administrative suite built for **Kayfa** — a leading Arabic e-learning platform offering specialized educational diplomas, tracks, and courses (Data Science, SOC Cybersecurity, Full-Stack Web Development, Artificial Intelligence, and more).

This platform acts as an intelligent assistant that engages visitors in interactive conversations, answers specific program questions using a RAG (Retrieval-Augmented Generation) pipeline, gauges buying signals, handles objections, and registers high-intent leads as CRM tickets. Additionally, it offers a secure admin portal containing usage analytics, cost dashboards, and step-by-step LLM reasoning traces.

---

## 🚀 Key Features

### 1. 🌐 Premium Bilingual Chat Interface
- **Dynamic RTL/LTR Direction**: Custom JavaScript and CSS override Streamlit's default styling, dynamically adjusting text alignment (`direction: rtl` / `direction: ltr`) and cursor position on-the-fly inside the user input box and chat bubbles.
- **Per-Paragraph Separation**: Mixed-language conversations are separated at the paragraph, heading, and list level, preventing text direction conflicts and mid-word breaks.
- **Cairo & Inter Fonts**: Integrated Google Fonts dynamically apply Cairo to Arabic texts (increasing readability and spacing) and Inter to English text.
- **Glassmorphism Design**: Beautiful modern UI built with clean gradients, interactive cards, micro-animations (bubble entrance, shimmer hover states), and full desktop/mobile responsiveness.

### 2. 🧠 Intelligent ReAct Orchestration Graph
- **State-aware Logic**: Categorizes conversation stages (`early` ➔ `exploring` ➔ `evaluating` ➔ `deciding` ➔ `converting`) and customer intents (`browsing`, `comparing`, `price_sensitive`, `ready_to_enroll`).
- **Autonomous RAG Tool Calling**: The agent decides when to query the Knowledge Base, retrieve detailed roadmaps, or trigger CRM registrations.
- **Lead Capture Guardrails**: Intelligently defers lead generation tools until strong purchase intent or contact-request signals are registered to provide value first.

### 3. 📚 Semantic RAG Vector Database
- **Custom Ingestion Pipeline**: Ingests, parses, and splits unstructured course structures, roadmap paths, refund policies, FAQs, and corporate overviews into logical H2 sections.
- **ChromaDB**: Persists local dense embeddings (utilizing OpenAI or Gemini embedding models) to query highly relevant documents during chats.

### 4. 💼 Integrated Lead CRM Management (Admin Only)
- **Automatic Entity Extraction**: Spawns parallel LLM calls to parse Arabic/English transcripts, capturing names, phone numbers, emails, target programs, locations, buying triggers, objections, and next-action steps.
- **Ticketing Dashboard**: Features comprehensive lead lifecycle tracking (`new` ➔ `contacted` ➔ `qualified` ➔ `closed`), interactive status transition triggers, quick-action deletions, and phone/email links.

### 5. 📊 Real-time Cost & Performance Auditing (Admin Only)
- **Granular Token Estimation**: Tracks and maps token usage to provider-specific tables (OpenAI, Gemini, Groq, OpenRouter) to calculate real API costs.
- **Visual Analytics**: Interactive daily cost trends, total token consumption graphs, and logs.

### 6. 🔍 Step-by-Step Behaviour Decision Tracer (Admin Only)
- **Deep Execution Tracing**: Unpacks intermediate thoughts, LLM queries, tool parameters, execution statuses, and token expenses per run ID for prompt engineering and debugging.

---

## 📂 Directory Structure

```text
kayfa-sales-agent-last-version/
├── app/
│   ├── Home.py                  # Entrypoint & authentication gate (login/signup dashboard)
│   ├── sidebar_helper.py        # Centralized navigation management (role-based hiding)
│   ├── logo.png                 # App logo
│   └── pages/
│       ├── 1_Chat_Agent.py      # Core chat client (bilingual overrides & styles)
│       ├── 2_CRM_Tickets.py     # CRM admin dashboard & update tools
│       ├── 3_Cost_Monitor.py    # Cost charts & usage metrics dashboard
│       └── 4_Behaviour_Trace.py # Step-by-step agent reasoning logs
├── agent/
│   ├── tools.py                 # Tools mapping (search_kb, get_roadmap, create_lead_ticket)
│   ├── prompts.py               # Bilingual system prompting & CRM structured extractions
│   ├── graph.py                 # Agent ReAct loop loop, intent classifications & guardrails
│   └── usage_logger.py          # Log writers mapping database writes for usage/behaviors
├── core/
│   ├── auth.py                  # BCrypt password hashing & session management
│   ├── db.py                    # MongoDB database driver & collection client pools
│   └── config.py                # Environment parser & provider-agnostic token cost maps
├── rag/
│   ├── ingest.py                # Ingestion scripts (parses catalog files ➔ ChromaDB chunks)
│   ├── retriever.py             # Vector store access interfaces & query engines
│   └── vectorstore/             # Chroma database storage folder (gitignored)
├── data/
│   ├── json/                    # Structured course catalogs & roadmap configurations
│   └── text/                    # Markdown documents on accreditation, FAQ, refunds, policies
├── requirements.txt             # PyPI packages mapping
└── .env                         # Environmental settings file
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python**: v3.10+ (recommended v3.12)
- **MongoDB**: Active local instance or MongoDB Atlas cluster connection string
- **LLM API Key**: Google Gemini API key (recommended), Groq API key, or OpenAI API key

### 2. Clone and Setup Environment
Navigate to the project root and create a virtual environment:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure `.env` File
Create a `.env` file in the root directory:
```env
# --- LLM API Providers (Provide at least one) ---
GEMINI_API_KEY="your-gemini-api-key-here"
GEMINI_MODEL="gemini-2.0-flash"
GEMINI_EMBEDDING_MODEL="text-embedding-004"

# Optional Fallbacks
OPENAI_API_KEY=""
OPENAI_CHAT_MODEL="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

GROQ_API_KEY=""
GROQ_MODEL="llama-3.3-70b-versatile"

# --- MongoDB Connections ---
MONGODB_URI="mongodb://localhost:27017"
MONGODB_DB_NAME="kayfa_sales_agent"

# --- App Settings ---
APP_DEBUG="false"
LOG_LEVEL="INFO"
```

---

## 💾 Data Ingestion (KB Vector Store Setup)

Before running the application, populate the vector store with Kayfa's course contents and markdown guidelines.

To ingest the data in `data/json/` and `data/text/` and construct the Chroma vector store, run:
```bash
python -m rag.ingest
```
This script will:
1. Load courses from `kayfa_courses.json`
2. Load roadmaps from `kayfa_roadmaps.json`
3. Parse markdown text sections in `data/text/`
4. Split files using header boundaries, generate embeddings, and build the local database under `rag/vectorstore/`.

---

## 🚀 Running the Application

Launch the Streamlit dashboard:
```bash
streamlit run app/Home.py
```

### Access Roles Setup
By default, newly registered users get the `"visitor"` role, granting access to the **Chat Agent** page. 

To grant a user **admin** access (enabling the CRM, Cost Monitor, and Behaviour Trace sections):
1. Connect to your MongoDB instance.
2. Open the `users` collection under the configured database (default `kayfa_sales_agent`).
3. Find your registered user document and update the `"role"` field from `"visitor"` to `"admin"`:
   ```json
   { "role": "admin" }
   ```
4. Reload the page or log back in. The custom sidebar will dynamically render the administrative panels.
