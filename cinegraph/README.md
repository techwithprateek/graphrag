# 🎬 CineGraph — GraphRAG Demo

> **Prove that graph traversal beats vector RAG for relationship-heavy queries — visually, interactively, in real time.**

CineGraph is a demo application built on **TMDB movie data** and **Neo4j AuraDB**. Ask a natural-language question, watch a force-directed graph animate on screen, read the generated Cypher query, and get an AI answer — all powered by graph traversal, zero embeddings.

---

## 🧠 What is GraphRAG?

Standard RAG splits documents into chunks, embeds them, and retrieves the most similar ones. It works well for *"What year was The Matrix released?"* — but completely breaks down for relational questions like:

- *"Which actors worked with both Tom Hanks **and** Meg Ryan?"* → requires set intersection across two paths
- *"How is Kevin Bacon connected to Tom Hanks?"* → requires shortest-path traversal across 4+ hops
- *"Actors in Nolan films who never co-starred together?"* → requires exclusion reasoning over a graph complement

**No chunk size, no re-ranking strategy, no retrieval k can fix this.** The operations are structurally absent from the vector RAG paradigm. Graph traversal is the only answer.

---

## ✨ Features

- 🔍 **Natural language → Cypher** — GPT-4o generates Cypher queries from plain English
- 🕸️ **Live graph visualization** — force-directed subgraph renders for every query
- 💬 **Conversational answers** — LLM synthesizes results into readable prose
- ⚡ **7 demo questions** — from 1-hop warmups to 4+ hop shortest paths
- 🎨 **Color-coded nodes** — Movies, People, Genres, and Studios each have distinct colors
- 🚫 **No vector DB, no embeddings** — pure graph retrieval from start to finish

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| 🔙 **Backend** | Python 3.11+, FastAPI |
| 🤖 **LLM** | OpenAI GPT-4o |
| 🗄️ **Graph DB** | Neo4j AuraDB (free tier) |
| 🖥️ **Frontend** | Streamlit |
| 📊 **Graph Viz** | streamlit-agraph |
| 🌐 **HTTP Client** | httpx |

> **100% Python.** No Node.js, no Docker, no npm. A single `pip install -r requirements.txt` installs everything.

---

## 📋 Prerequisites

Before you start, make sure you have:

| Requirement | Notes |
|---|---|
| 🐍 **Python 3.11+** | Check with `python3 --version` |
| ☁️ **Neo4j AuraDB account** | Free tier at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/) — no local install needed |
| 🔑 **OpenAI API key** | GPT-4o access at [platform.openai.com](https://platform.openai.com/api-keys) |
| 🎬 **TMDB API key** | Free key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) |

---

## 🚀 Getting Started

### Step 1 — Clone & Install

```bash
git clone https://github.com/techwithprateek/graphrag
cd graphrag/cinegraph
pip install -r requirements.txt
```

### Step 2 — Configure Credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```bash
OPENAI_API_KEY=sk-...
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
TMDB_API_KEY=your-tmdb-key
```

### Step 3 — Seed the Database

```bash
python3 seed/load_tmdb.py
```

This downloads ~200 popular movies from the TMDB API — cast, crew, genres, and production studios — and loads them into Neo4j as a rich property graph. Takes about 2–3 minutes.

### Step 4 — Start the Backend

```bash
# Terminal 1
uvicorn backend.main:app --reload
```

Backend runs at **http://localhost:8000**

### Step 5 — Start the Frontend

```bash
# Terminal 2
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser. 🎉

---

## 🗂️ Project Structure

```
cinegraph/
│
├── 🔙 backend/
│   ├── main.py                  # FastAPI app · CORS · route registration
│   ├── config.py                # Loads credentials from .env
│   ├── models.py                # Pydantic request & response models
│   │
│   ├── routes/
│   │   ├── query.py             # POST /api/query — LLM + Neo4j orchestration
│   │   └── schema.py            # GET /api/schema · /api/examples · /health
│   │
│   ├── services/
│   │   ├── neo4j_service.py     # Async Neo4j driver · Cypher execution · graph builder
│   │   └── llm_service.py       # GPT-4o: generate_cypher() + synthesize_answer()
│   │
│   └── prompts/
│       └── cypher_prompt.py     # System prompts · few-shot Cypher examples
│
├── 🖥️ frontend/
│   └── app.py                   # Entire Streamlit UI in one file
│
├── 🌱 seed/
│   └── load_tmdb.py             # Downloads TMDB data → loads into Neo4j
│
├── requirements.txt             # All Python dependencies
├── .env.example                 # Credential template
└── README.md
```

---

## 🎯 Demo Walkthrough

Click these example questions in the UI sidebar to see GraphRAG in action:

| # | Question | Why it needs graph traversal |
|---|---|---|
| 1️⃣ | *[1 hop] Which movies did Tom Hanks act in?* | Warmup — single `ACTED_IN` edge |
| 2️⃣ | *[2 hops] Which actors worked with both Tom Hanks and Meg Ryan?* | Set intersection across two actor→movie paths |
| 3️⃣ | *[2 hops] Which directors have worked with Keanu Reeves more than once?* | Edge-count aggregation |
| 4️⃣ | *[3 hops] Which actor has appeared in the most genres?* | Cross-entity aggregation: Person→Movie→Genre |
| 5️⃣ | *[4+ hops] How is Kevin Bacon connected to Tom Hanks?* | 🌟 **Showpiece** — `shortestPath()` across the graph |
| 6️⃣ | *[3 hops] Which movies share the director and genre of The Matrix?* | Multi-condition graph join |
| 7️⃣ | *[3 hops + exclusion] Actors in Nolan films who never co-starred together?* | Exclusion reasoning — impossible for vector RAG |

**What to watch:** Column 2 shows the live graph. Column 3 shows the exact Cypher that was executed — it walks edges, it doesn't search text.

---

## 🎨 Graph Node Colors

| Color | Node Type |
|---|---|
| 🔴 `#E8593C` Coral | 🎬 Movie |
| 🟣 `#7F77DD` Purple | 🧑 Person (Actor / Director / Writer) |
| 🟢 `#1D9E75` Teal | 🎭 Genre |
| 🟡 `#BA7517` Amber | 🏢 Studio |

---

## ❓ Why Not Vector RAG?

Vector RAG retrieves text chunks by embedding similarity. It fails on relational queries because:

**🔗 Shortest path (Q5):** The connection between Kevin Bacon and Tom Hanks is a *path* across 4+ relationship hops. No text chunk contains this path. Even retrieving all chunks mentioning both actors gives you a bag of facts, not a traversal route. Only `shortestPath()` in Cypher can answer this.

**🚫 Exclusion reasoning (Q7):** Finding actors who *never* co-starred requires computing the complement of a relationship set. This is a structural graph operation. It cannot be approximated by any combination of embedding retrieval, re-ranking, or prompt engineering.

These aren't edge cases — they're the majority of interesting questions about connected data.

---

## 📡 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `GET` | `/api/schema` | Neo4j node labels, relationship types, property keys |
| `GET` | `/api/examples` | The 7 demo questions |
| `POST` | `/api/query` | Main endpoint: question → Cypher → answer + graph |

---

*Built with ❤️ to show that for relationship-heavy data, the graph wins.*
