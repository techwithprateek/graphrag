import httpx
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

BACKEND = "http://localhost:8000"

# Node colors by label
NODE_COLORS = {
    "Movie":  "#E8593C",
    "Person": "#7F77DD",
    "Genre":  "#1D9E75",
    "Studio": "#BA7517",
}
NODE_SIZES = {"Movie": 25, "Person": 20, "Genre": 15, "Studio": 15}

st.set_page_config(page_title="CineGraph", layout="wide")

# ── Health check on startup ──────────────────────────────────────────────────
try:
    httpx.get(f"{BACKEND}/api/health", timeout=2).raise_for_status()
except Exception:
    st.error("⚠️ Backend not reachable. Start it with: uvicorn backend.main:app --reload")
    st.stop()


# ── Schema (cached 5 min) ────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_schema():
    return httpx.get(f"{BACKEND}/api/schema", timeout=5).json()


@st.cache_data(ttl=300)
def fetch_examples():
    return httpx.get(f"{BACKEND}/api/examples", timeout=5).json()["examples"]


# ── Session state defaults ───────────────────────────────────────────────────
if "question" not in st.session_state:
    st.session_state.question = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "run_query" not in st.session_state:
    st.session_state.run_query = False


# ── Layout: three columns ────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])

# ── Column 1: Controls ───────────────────────────────────────────────────────
with col1:
    st.title("CineGraph")
    st.caption("GraphRAG Demo · TMDB + Neo4j")

    question_input = st.text_area(
        "Ask a question about movies",
        value=st.session_state.question,
        height=100,
        key="question_input",
    )

    if st.button("Ask", type="primary"):
        st.session_state.question = question_input
        st.session_state.run_query = True

    st.divider()
    st.subheader("Try an example")

    for example in fetch_examples():
        if st.button(example, key=example):
            st.session_state.question = example
            st.session_state.run_query = True
            st.rerun()

    st.divider()
    with st.expander("Graph Schema"):
        schema_data = fetch_schema()
        st.markdown("**Node labels:** " + ", ".join(f"`{l}`" for l in schema_data.get("labels", [])))
        st.markdown("**Relationships:** " + ", ".join(f"`{r}`" for r in schema_data.get("relationship_types", [])))

    st.info(
        "**Why Graph RAG?**\n\n"
        "Graph traversal resolves multi-hop relational questions by literally walking edges "
        "— something vector similarity search cannot do regardless of chunk size or retrieval k. "
        "Questions like 'How is Kevin Bacon connected to Tom Hanks?' require path-finding across "
        "the graph, not text matching."
    )

# ── Run query if flagged ─────────────────────────────────────────────────────
if st.session_state.run_query and st.session_state.question:
    st.session_state.run_query = False
    with col2:
        with st.spinner("Traversing the graph…"):
            try:
                response = httpx.post(
                    f"{BACKEND}/api/query",
                    json={"question": st.session_state.question},
                    timeout=60,
                )
                st.session_state.result = response.json()
            except Exception as e:
                st.session_state.result = {"error": True, "detail": str(e)}

# ── Column 2: Graph canvas ───────────────────────────────────────────────────
with col2:
    result = st.session_state.result

    if result is None:
        st.info("Ask a question or pick an example to see the graph")
    elif result.get("error"):
        st.error(result.get("detail", "Unknown error"))
    else:
        graph_data = result.get("graph_data", {})
        raw_nodes = graph_data.get("nodes", [])
        raw_edges = graph_data.get("edges", [])

        if not raw_nodes:
            st.warning("Query returned no results. Try rephrasing.")
        else:
            agraph_nodes = [
                Node(
                    id=n["id"],
                    label=n["properties"].get("display", n["id"]),
                    size=NODE_SIZES.get(n["label"], 15),
                    color=NODE_COLORS.get(n["label"], "#888888"),
                )
                for n in raw_nodes
            ]
            agraph_edges = [
                Edge(source=e["source"], target=e["target"], label=e["type"])
                for e in raw_edges
            ]
            config = Config(
                height=580,
                width="100%",
                directed=True,
                physics=True,
                hierarchical=False,
            )
            agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)

# ── Column 3: Answer + Cypher ────────────────────────────────────────────────
with col3:
    result = st.session_state.result
    if result and not result.get("error"):
        st.subheader("Answer")
        st.markdown(result["answer"])

        st.divider()
        st.subheader("Generated Cypher")
        st.code(result["cypher"], language="cypher")

        st.divider()
        meta = result.get("meta", {})
        m1, m2, m3 = st.columns(3)
        m1.metric("Nodes", meta.get("node_count", 0))
        m2.metric("Edges", meta.get("edge_count", 0))
        m3.metric("Time", f"{meta.get('query_ms', 0)} ms")

        st.caption(f"This query traversed {result.get('hop_count', 1)} hop(s) across the graph.")
