import json
import re
import asyncio
import logging

import anthropic

from .prompts import COMMON_PREAMBLE, MATERIAL_PROMPTS, TOPIC_SCHEMA_INSTRUCTION


def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()

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
        logger.info("  Mapping: %s", doc["filename"])
        for attempt in range(max_retries):
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                text = strip_markdown_fences(response.content[0].text)
                result = json.loads(text)
                logger.info("  Done:    %s", doc["filename"])
                return result

            except (json.JSONDecodeError, KeyError):
                logger.warning("  Retry:   %s (bad JSON, attempt %d/%d)", doc["filename"], attempt + 1, max_retries)
            except anthropic.APIError as e:
                logger.warning("  Retry:   %s (API error, attempt %d/%d)", doc["filename"], attempt + 1, max_retries)

        logger.error("  FAILED:  %s", doc["filename"])
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
    logger.info("Phase 1 complete: %d/%d documents succeeded", len(topic_trees), len(documents))
    return topic_trees
