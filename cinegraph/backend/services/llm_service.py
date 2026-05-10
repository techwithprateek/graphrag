from openai import AsyncOpenAI
from backend.config import settings
from backend.prompts.cypher_prompt import CYPHER_SYSTEM_PROMPT, ANSWER_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_cypher(question: str) -> str:
    """Ask GPT-4o to produce a Cypher query for the given question."""
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CYPHER_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


async def synthesize_answer(question: str, cypher: str, results: list[dict]) -> str:
    """Ask GPT-4o to turn raw query results into a conversational answer."""
    user_content = f"""Question: {question}

Cypher query used:
{cypher}

Query results (raw):
{results}"""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
