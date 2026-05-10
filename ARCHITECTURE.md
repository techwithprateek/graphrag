# 🎬 CineGraph — Architecture Diagrams

---

## 1. System Architecture

```mermaid
graph TB
    subgraph User["👤 User"]
        Browser["🌐 Browser\nlocalhost:8501"]
    end

    subgraph Frontend["🖥️ Frontend — Streamlit (port 8501)"]
        UI["app.py\n─────────────\n• Health check on load\n• 3-column layout\n• Example question buttons\n• agraph canvas\n• Session state"]
    end

    subgraph Backend["🔙 Backend — FastAPI (port 8000)"]
        direction TB
        Main["main.py\nFastAPI + CORS"]
        RouteQ["routes/query.py\nPOST /api/query"]
        RouteS["routes/schema.py\nGET /api/schema\nGET /api/examples\nGET /health"]
        LLM["services/llm_service.py\n─────────────\ngenerate_cypher()\nsynthesize_answer()"]
        Neo4jSvc["services/neo4j_service.py\n─────────────\nrun_cypher()\nbuild_graph_data()\nget_schema()"]
        Prompt["prompts/cypher_prompt.py\n─────────────\nSystem prompt\nFew-shot examples"]

        Main --> RouteQ
        Main --> RouteS
        RouteQ --> LLM
        RouteQ --> Neo4jSvc
        LLM --> Prompt
    end

    subgraph External["☁️ External Services"]
        OpenAI["🤖 OpenAI\nGPT-4o"]
        Neo4j["🗄️ Neo4j AuraDB\nFree Tier"]
        TMDB["🎬 TMDB API\nMovie Data"]
    end

    subgraph Seed["🌱 Seed Script"]
        SeedScript["seed/load_tmdb.py\n─────────────\nFetch movies\nExtract cast/crew\nLoad into Neo4j"]
    end

    Browser -->|"HTTP request"| UI
    UI -->|"httpx POST /api/query"| Main
    UI -->|"httpx GET /api/health\n/api/schema\n/api/examples"| Main
    LLM -->|"Chat Completions API"| OpenAI
    Neo4jSvc -->|"Async Cypher queries"| Neo4j
    SeedScript -->|"Fetch popular movies\npages 1–10"| TMDB
    SeedScript -->|"MERGE nodes\n& relationships"| Neo4j

    style User fill:#f0f4ff,stroke:#4a6fa5
    style Frontend fill:#e8f5e9,stroke:#2e7d32
    style Backend fill:#fff3e0,stroke:#e65100
    style External fill:#fce4ec,stroke:#c62828
    style Seed fill:#e8eaf6,stroke:#3949ab
```

---

## 2. Request Flow — POST /api/query

```mermaid
sequenceDiagram
    actor User
    participant ST as 🖥️ Streamlit
    participant FA as 🔙 FastAPI
    participant LLM as 🤖 GPT-4o
    participant N4J as 🗄️ Neo4j AuraDB

    User->>ST: Types question & clicks Ask
    ST->>FA: POST /api/query {"question": "..."}

    FA->>LLM: System prompt + schema + question
    Note over LLM: Generates Cypher query<br/>from few-shot examples
    LLM-->>FA: "MATCH (p:Person)..."

    FA->>N4J: Execute Cypher (async)
    Note over N4J: Graph traversal<br/>walks edges
    N4J-->>FA: Raw records (nodes + rels)

    FA->>FA: build_graph_data(records)
    Note over FA: Extract Node / Relationship<br/>/ Path objects → JSON

    FA->>LLM: Question + Cypher + raw results
    Note over LLM: Synthesizes conversational<br/>answer with citations
    LLM-->>FA: Natural language answer

    FA-->>ST: {answer, cypher, graph_data, meta}

    ST->>ST: Render agraph canvas
    ST->>ST: Display Cypher + metrics
    ST-->>User: Graph + Answer + Cypher
```

---

## 3. Neo4j Graph Schema

```mermaid
graph LR
    Person["🧑 Person\n──────\nname\nborn"]
    Movie["🎬 Movie\n──────\ntitle\nyear\ntagline\nrevenue\nrating"]
    Genre["🎭 Genre\n──────\nname"]
    Studio["🏢 Studio\n──────\nname"]

    Person -->|"ACTED_IN\n{roles}"| Movie
    Person -->|"DIRECTED"| Movie
    Person -->|"WROTE"| Movie
    Movie -->|"IN_GENRE"| Genre
    Movie -->|"PRODUCED_BY"| Studio

    style Person fill:#7F77DD,color:#fff,stroke:#5a52b0
    style Movie fill:#E8593C,color:#fff,stroke:#b03a1e
    style Genre fill:#1D9E75,color:#fff,stroke:#117a55
    style Studio fill:#BA7517,color:#fff,stroke:#8a5510
```

---

## 4. Data Seeding Flow

```mermaid
flowchart TD
    Start(["▶️ python seed/load_tmdb.py"])
    CheckEnv{"✅ .env vars\npresent?"}
    Fail(["❌ Exit with\nmissing vars error"])
    FetchList["📥 Fetch popular movies\nfrom TMDB API\n(10 pages × 20 movies)"]
    Connect["🔌 Connect to\nNeo4j AuraDB"]
    Clear["🗑️ Clear existing data\nMATCH (n) DETACH DELETE n"]
    Constraints["🔑 Create uniqueness\nconstraints"]
    Loop["🔄 For each movie"]
    Details["📋 Fetch full details\n+ credits from TMDB"]
    LoadMovie["MERGE (:Movie)"]
    LoadGenres["MERGE (:Genre)\n(:Movie)-[:IN_GENRE]→(:Genre)"]
    LoadStudios["MERGE (:Studio)\n(:Movie)-[:PRODUCED_BY]→(:Studio)"]
    LoadCast["MERGE (:Person)\n(:Person)-[:ACTED_IN]→(:Movie)"]
    LoadCrew["MERGE (:Person)\n(:Person)-[:DIRECTED/:WROTE]→(:Movie)"]
    Done(["🎉 Done!\n~200 movies loaded"])

    Start --> CheckEnv
    CheckEnv -->|No| Fail
    CheckEnv -->|Yes| FetchList
    FetchList --> Connect
    Connect --> Clear
    Clear --> Constraints
    Constraints --> Loop
    Loop --> Details
    Details --> LoadMovie
    LoadMovie --> LoadGenres
    LoadGenres --> LoadStudios
    LoadStudios --> LoadCast
    LoadCast --> LoadCrew
    LoadCrew -->|next movie| Loop
    Loop -->|all done| Done

    style Start fill:#4caf50,color:#fff
    style Done fill:#4caf50,color:#fff
    style Fail fill:#f44336,color:#fff
    style CheckEnv fill:#ff9800,color:#fff
```

---

## 5. Frontend Layout

```mermaid
graph TD
    subgraph App["🖥️ Streamlit App — localhost:8501"]
        HC["🔴 Health Check on Load\nGET /api/health → stop if unreachable"]

        subgraph Cols["st.columns([1, 2, 1])"]
            subgraph C1["📋 Column 1 — Controls"]
                Title["CineGraph title + caption"]
                TextArea["st.text_area — question input"]
                AskBtn["st.button('Ask') — primary"]
                Examples["Example buttons × 7\n(click → immediate query)"]
                SchemaExp["st.expander('Graph Schema')\ncached st.cache_data ttl=300"]
                InfoBox["st.info — Why Graph RAG?"]
            end

            subgraph C2["🕸️ Column 2 — Graph Canvas"]
                Spinner["st.spinner while loading"]
                AGraph["agraph(nodes, edges, config)\nforce-directed · physics=True"]
                NoResult["st.warning if 0 nodes"]
                Empty["st.info if no query yet"]
            end

            subgraph C3["💬 Column 3 — Answer + Cypher"]
                Answer["st.subheader + st.markdown\nNatural language answer"]
                Cypher["st.code(cypher, language='cypher')"]
                Metrics["st.columns(3)\nNodes · Edges · Time ms"]
                HopCap["st.caption — hop count"]
            end
        end
    end

    HC --> Cols
    C1 --> C2
    C2 --> C3
```
