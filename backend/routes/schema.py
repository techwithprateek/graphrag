from fastapi import APIRouter
from backend.services.neo4j_service import get_schema

router = APIRouter()

EXAMPLE_QUESTIONS = [
    "[1 hop] Which movies did Tom Hanks act in?",
    "[2 hops] Which actors worked with both Tom Hanks and Meg Ryan?",
    "[2 hops] Which directors have worked with Keanu Reeves more than once?",
    "[3 hops] Which actor has appeared in the most genres?",
    "[4+ hops] How is Kevin Bacon connected to Tom Hanks?",
    "[3 hops] Which movies share the director and genre of The Matrix?",
    "[3 hops + exclusion] Actors in Nolan films who never co-starred together?",
]


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/schema")
async def schema():
    return await get_schema()


@router.get("/examples")
async def examples():
    return {"examples": EXAMPLE_QUESTIONS}
