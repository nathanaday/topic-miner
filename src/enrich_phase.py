import json
import logging

import anthropic

from .map_phase import strip_markdown_fences

from .prompts import ENRICH_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

TOKEN_LIMIT = 195_000  # stay under the 200k API limit


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def enrich_batch(nodes: list[dict], client: anthropic.Anthropic,
                 model: str, max_tokens: int, system_prompt: str,
                 max_retries: int = 3) -> list[dict]:
    tree_json = json.dumps(nodes, indent=2)
    user_prompt = f"Enrich and score this topic tree:\n\n{tree_json}"

    est_tokens = estimate_tokens(system_prompt + user_prompt)
    if est_tokens > TOKEN_LIMIT:
        logger.warning("  Enrich prompt too large (~%dk tokens), skipping", est_tokens // 1000)
        return None

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            if response.stop_reason == "max_tokens":
                return None

            text = strip_markdown_fences(response.content[0].text)
            enriched = json.loads(text)

            if isinstance(enriched, dict) and "topics" in enriched:
                enriched = enriched["topics"]

            return enriched

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("  Enrich batch bad JSON (attempt %d/%d): %s", attempt + 1, max_retries, e)
        except anthropic.APIError as e:
            logger.warning("  Enrich batch API error (attempt %d/%d): %s", attempt + 1, max_retries, e)

    return None


def assign_ids(nodes: list[dict], prefix: str = "topic"):
    for i, node in enumerate(nodes, 1):
        node_id = f"{prefix}_{i:03d}"
        node["id"] = node_id
        assign_ids(node.get("subtopics", []), node_id)


def run_enrich_phase(merged_tree: list[dict], config: dict) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_enrich"]
    weights = config["scoring_weights"]

    client = anthropic.Anthropic(api_key=config["api_key"])
    system_prompt = ENRICH_PROMPT_TEMPLATE.format(**weights)

    # Try enriching the whole tree at once
    logger.info("  Enriching full tree (%d top-level concepts)...", len(merged_tree))
    result = enrich_batch(merged_tree, client, model, max_tokens, system_prompt)

    if result is not None:
        logger.info("Phase 3 complete")
        assign_ids(result)
        return result

    # Tree too large -- enrich each top-level concept separately
    logger.info("  Tree too large, enriching per-concept (%d concepts)...", len(merged_tree))
    enriched = []
    for i, concept in enumerate(merged_tree):
        label = concept.get("topic", f"concept {i+1}")
        logger.info("  Enriching: %s (%d/%d)", label, i + 1, len(merged_tree))

        result = enrich_batch([concept], client, model, max_tokens, system_prompt)

        if result is not None:
            enriched.extend(result)
        else:
            logger.warning("  Failed to enrich: %s -- keeping unscored", label)
            enriched.append(concept)

    assign_ids(enriched)
    logger.info("Phase 3 complete: %d concepts enriched", len(enriched))
    return enriched
