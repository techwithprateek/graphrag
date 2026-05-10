"""
seed/load_tmdb.py
-----------------
Downloads popular movies from the TMDB API and loads them into Neo4j AuraDB.

Usage:
    cd cinegraph
    python seed/load_tmdb.py

Requires .env with:
    TMDB_API_KEY=...
    NEO4J_URI=...
    NEO4J_USERNAME=...
    NEO4J_PASSWORD=...
"""

import os
import sys
import httpx
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
TMDB_BASE = "https://api.themoviedb.org/3"

# How many pages of popular movies to fetch (20 movies per page)
PAGES_TO_FETCH = 10


def check_config():
    missing = [k for k, v in {
        "TMDB_API_KEY": TMDB_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
    }.items() if not v]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        print("   Copy .env.example → .env and fill in your credentials.")
        sys.exit(1)


# ── TMDB fetchers ────────────────────────────────────────────────────────────

def fetch_popular_movies(pages: int) -> list[dict]:
    movies = []
    print(f"📥 Fetching {pages} pages of popular movies from TMDB…")
    for page in range(1, pages + 1):
        resp = httpx.get(
            f"{TMDB_BASE}/movie/popular",
            params={"api_key": TMDB_API_KEY, "page": page},
            timeout=15,
        )
        resp.raise_for_status()
        movies.extend(resp.json()["results"])
        print(f"   Page {page}/{pages} — {len(movies)} movies so far")
    return movies


def fetch_movie_details(movie_id: int) -> dict:
    """Fetch full details (genres, production companies, credits) for one movie."""
    resp = httpx.get(
        f"{TMDB_BASE}/movie/{movie_id}",
        params={"api_key": TMDB_API_KEY, "append_to_response": "credits"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Neo4j loader ─────────────────────────────────────────────────────────────

def clear_database(session):
    print("🗑️  Clearing existing data…")
    session.run("MATCH (n) DETACH DELETE n")


def create_constraints(session):
    print("🔑 Creating uniqueness constraints…")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie)  REQUIRE m.tmdb_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.tmdb_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Genre)  REQUIRE g.name    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Studio) REQUIRE s.name    IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)


def load_movie(session, details: dict):
    movie_id = details["id"]
    title = details.get("title", "Unknown")

    # Upsert Movie node
    session.run(
        """
        MERGE (m:Movie {tmdb_id: $tmdb_id})
        SET m.title    = $title,
            m.year     = $year,
            m.tagline  = $tagline,
            m.revenue  = $revenue,
            m.rating   = $rating
        """,
        tmdb_id=movie_id,
        title=title,
        year=int(details.get("release_date", "0000")[:4] or 0),
        tagline=details.get("tagline", ""),
        revenue=details.get("revenue", 0),
        rating=details.get("vote_average", 0.0),
    )

    # Genres → (:Movie)-[:IN_GENRE]->(:Genre)
    for genre in details.get("genres", []):
        session.run(
            """
            MERGE (g:Genre {name: $name})
            WITH g
            MATCH (m:Movie {tmdb_id: $tmdb_id})
            MERGE (m)-[:IN_GENRE]->(g)
            """,
            name=genre["name"],
            tmdb_id=movie_id,
        )

    # Studios → (:Movie)-[:PRODUCED_BY]->(:Studio)
    for company in details.get("production_companies", [])[:3]:  # top 3 studios
        session.run(
            """
            MERGE (s:Studio {name: $name})
            WITH s
            MATCH (m:Movie {tmdb_id: $tmdb_id})
            MERGE (m)-[:PRODUCED_BY]->(s)
            """,
            name=company["name"],
            tmdb_id=movie_id,
        )

    credits = details.get("credits", {})

    # Cast → (:Person)-[:ACTED_IN {roles}]->(:Movie)
    for member in credits.get("cast", [])[:15]:  # top 15 cast members
        person_id = member["id"]
        session.run(
            """
            MERGE (p:Person {tmdb_id: $person_id})
            SET p.name = $name,
                p.born = $born
            WITH p
            MATCH (m:Movie {tmdb_id: $tmdb_id})
            MERGE (p)-[r:ACTED_IN]->(m)
            SET r.roles = $roles
            """,
            person_id=person_id,
            name=member.get("name", ""),
            born=0,
            tmdb_id=movie_id,
            roles=[member.get("character", "")],
        )

    # Crew: directors and writers
    for member in credits.get("crew", []):
        if member.get("job") not in ("Director", "Writer", "Screenplay"):
            continue
        person_id = member["id"]
        rel_type = "DIRECTED" if member["job"] == "Director" else "WROTE"
        session.run(
            f"""
            MERGE (p:Person {{tmdb_id: $person_id}})
            SET p.name = $name
            WITH p
            MATCH (m:Movie {{tmdb_id: $tmdb_id}})
            MERGE (p)-[:{rel_type}]->(m)
            """,
            person_id=person_id,
            name=member.get("name", ""),
            tmdb_id=movie_id,
        )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    check_config()

    # 1. Download movie list
    movies = fetch_popular_movies(PAGES_TO_FETCH)
    print(f"\n✅ Downloaded {len(movies)} movies\n")

    # 2. Connect to Neo4j
    print("🔌 Connecting to Neo4j…")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("   Connected!\n")

    with driver.session() as session:
        clear_database(session)
        create_constraints(session)

        print(f"📤 Loading {len(movies)} movies into Neo4j…")
        for i, movie in enumerate(movies, 1):
            try:
                details = fetch_movie_details(movie["id"])
                load_movie(session, details)
                if i % 10 == 0:
                    print(f"   Loaded {i}/{len(movies)} movies")
            except Exception as e:
                print(f"   ⚠️  Skipped movie {movie.get('title', movie['id'])}: {e}")

    driver.close()
    print(f"\n🎉 Done! {len(movies)} movies loaded into Neo4j.")
    print("   You can now start the backend and frontend:")
    print("   Terminal 1: uvicorn backend.main:app --reload")
    print("   Terminal 2: streamlit run frontend/app.py")


if __name__ == "__main__":
    main()
