import json
import os
import re
import asyncio
import logging

import anthropic

from .prompts import COMMON_PREAMBLE, MATERIAL_PROMPTS, TOPIC_SCHEMA_INSTRUCTION

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = "map_output"
CHECKPOINT_LOG = os.path.join(CHECKPOINT_DIR, "completed.txt")


def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def init_checkpoint_dir():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    if not os.path.exists(CHECKPOINT_LOG):
        with open(CHECKPOINT_LOG, "w") as f:
            pass


def load_completed() -> set[str]:
    if not os.path.exists(CHECKPOINT_LOG):
        return set()
    with open(CHECKPOINT_LOG, "r") as f:
        return {line.strip() for line in f if line.strip()}


def find_cached_parts(doc_id: str, completed: set[str]) -> list[str]:
    """Find all completed entries that are parts of this doc_id."""
    prefix = doc_id + "_part"
    return sorted([c for c in completed if c.startswith(prefix)])


def mark_completed(doc_id: str):
    with open(CHECKPOINT_LOG, "a") as f:
        f.write(doc_id + "\n")


def save_map_result(doc_id: str, result: dict):
    path = os.path.join(CHECKPOINT_DIR, f"{doc_id}.json")
    with open(path, "w") as f:
        json.dump(result, f, indent=2)


def load_map_result(doc_id: str) -> dict:
    path = os.path.join(CHECKPOINT_DIR, f"{doc_id}.json")
    with open(path, "r") as f:
        return json.load(f)


def save_manifest(documents: list[dict]):
    manifest_path = os.path.join(CHECKPOINT_DIR, "manifest.txt")
    with open(manifest_path, "w") as f:
        for doc in documents:
            f.write(f"{doc['doc_id']}  {doc['material_type']:12s}  {doc['filename']}\n")


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


def split_doc_content(doc: dict) -> list[dict]:
    content = doc["content"]
    header_end = content.index("\n---\n") + len("\n---\n")
    header = content[:header_end]
    body = content[header_end:]

    body_lines = body.split("\n")
    mid = len(body_lines) // 2

    chunk_a = header + "\n".join(body_lines[:mid])
    chunk_b = header + "\n".join(body_lines[mid:])

    doc_a = dict(doc)
    doc_a["doc_id"] = f"{doc['doc_id']}_partA"
    doc_a["content"] = chunk_a

    doc_b = dict(doc)
    doc_b["doc_id"] = f"{doc['doc_id']}_partB"
    doc_b["content"] = chunk_b

    return [doc_a, doc_b]


async def extract_topics_async(doc: dict, client: anthropic.AsyncAnthropic,
                               model: str, max_tokens: int,
                               semaphore: asyncio.Semaphore,
                               max_retries: int = 3) -> list[dict]:
    system_prompt, user_prompt = build_map_prompt(doc)

    async with semaphore:
        logger.info("  Mapping: %s [%s]", doc["filename"], doc["doc_id"])
        for attempt in range(max_retries):
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                if response.stop_reason == "max_tokens":
                    logger.warning(
                        "  Truncated: %s -- output too long, splitting document",
                        doc["filename"]
                    )
                    return None

                text = strip_markdown_fences(response.content[0].text)
                result = json.loads(text)

                save_map_result(doc["doc_id"], result)
                mark_completed(doc["doc_id"])
                logger.info("  Done:    %s [%s]", doc["filename"], doc["doc_id"])
                return [result]

            except (json.JSONDecodeError, KeyError) as e:
                dump_path = f"bad_json_{doc['doc_id']}_attempt{attempt + 1}.txt"
                with open(dump_path, "w") as f:
                    f.write(text)
                logger.warning("  Retry:   %s (bad JSON, attempt %d/%d) -- dumped to %s", doc["filename"], attempt + 1, max_retries, dump_path)
                logger.warning("           Error: %s", e)
            except anthropic.APIError:
                logger.warning("  Retry:   %s (API error, attempt %d/%d)", doc["filename"], attempt + 1, max_retries)

        logger.error("  FAILED:  %s", doc["filename"])
        return None


async def map_document(doc: dict, client: anthropic.AsyncAnthropic,
                       model: str, max_tokens: int,
                       semaphore: asyncio.Semaphore,
                       completed: set[str]) -> list[dict]:
    doc_id = doc["doc_id"]

    # Check if this exact doc_id is cached
    if doc_id in completed:
        logger.info("  Cached:  %s [%s]", doc["filename"], doc_id)
        return [load_map_result(doc_id)]

    # Check if parts of this doc_id are cached
    cached_parts = find_cached_parts(doc_id, completed)
    if cached_parts:
        logger.info("  Cached:  %s [%s] (%d parts)", doc["filename"], doc_id, len(cached_parts))
        return [load_map_result(part_id) for part_id in cached_parts]

    # Not cached -- call the API
    results = await extract_topics_async(doc, client, model, max_tokens, semaphore)

    if results is not None:
        return results

    parts = split_doc_content(doc)
    logger.info("  Split %s into %d parts", doc["filename"], len(parts))

    all_results = []
    for part in parts:
        part_results = await map_document(part, client, model, max_tokens, semaphore, completed)
        all_results.extend(part_results)
    return all_results


async def run_map_phase(documents: list[dict], config: dict) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_map"]
    concurrency = config["llm"]["concurrency"]

    init_checkpoint_dir()
    save_manifest(documents)
    completed = load_completed()

    if completed:
        logger.info("Found %d cached results in %s", len(completed), CHECKPOINT_DIR)

    async_client = anthropic.AsyncAnthropic(api_key=config["api_key"])
    semaphore = asyncio.Semaphore(concurrency)

    tasks = [
        map_document(doc, async_client, model, max_tokens, semaphore, completed)
        for doc in documents
    ]
    nested_results = await asyncio.gather(*tasks)

    all_results = [r for batch in nested_results for r in batch]
    logger.info("Phase 1 complete: %d topic trees from %d documents", len(all_results), len(documents))
    return all_results
