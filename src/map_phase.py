import json
import asyncio
import logging

import anthropic

from .prompts import COMMON_PREAMBLE, MATERIAL_PROMPTS, TOPIC_SCHEMA_INSTRUCTION

logger = logging.getLogger(__name__)


def build_map_prompt(doc: dict) -> tuple[str, str]:
    material_type = doc["material_type"]
    material_instructions = MATERIAL_PROMPTS.get(material_type, MATERIAL_PROMPTS["student"])

    system_prompt = (
        f"{COMMON_PREAMBLE}\n\n"
        f"{material_instructions}\n\n"
        f"{TOPIC_SCHEMA_INSTRUCTION}"
    )

    user_prompt = (
        f"Extract the topic tree from this document.\n\n"
        f"Document ID: {doc['doc_id']}\n"
        f"Filename: {doc['filename']}\n"
        f"Material Type: {doc['material_type']}\n\n"
        f"{doc['content']}"
    )

    return system_prompt, user_prompt


async def extract_topics_async(doc: dict, client: anthropic.AsyncAnthropic,
                               model: str, max_tokens: int,
                               semaphore: asyncio.Semaphore,
                               max_retries: int = 3) -> dict | None:
    system_prompt, user_prompt = build_map_prompt(doc)

    async with semaphore:
        for attempt in range(max_retries):
            try:
                logger.info(
                    "Phase 1 [%s] %s (attempt %d)",
                    doc["doc_id"], doc["filename"], attempt + 1
                )

                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                text = response.content[0].text
                result = json.loads(text)
                logger.info("Phase 1 [%s] success", doc["doc_id"])
                return result

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Phase 1 [%s] malformed JSON (attempt %d): %s",
                    doc["doc_id"], attempt + 1, e
                )
            except anthropic.APIError as e:
                logger.warning(
                    "Phase 1 [%s] API error (attempt %d): %s",
                    doc["doc_id"], attempt + 1, e
                )

        logger.error("Phase 1 [%s] failed after %d retries", doc["doc_id"], max_retries)
        return None


async def run_map_phase(documents: list[dict], config: dict) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_map"]
    concurrency = config["llm"]["concurrency"]

    async_client = anthropic.AsyncAnthropic(api_key=config["api_key"])
    semaphore = asyncio.Semaphore(concurrency)

    tasks = [
        extract_topics_async(doc, async_client, model, max_tokens, semaphore)
        for doc in documents
    ]
    results = await asyncio.gather(*tasks)

    topic_trees = [r for r in results if r is not None]
    logger.info(
        "Phase 1 complete: %d/%d documents processed",
        len(topic_trees), len(documents)
    )
    return topic_trees
