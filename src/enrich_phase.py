import json
import logging

import anthropic

from .prompts import ENRICH_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


def run_enrich_phase(merged_tree: list[dict], config: dict,
                     max_retries: int = 3) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_enrich"]
    weights = config["scoring_weights"]

    client = anthropic.Anthropic(api_key=config["api_key"])

    system_prompt = ENRICH_PROMPT_TEMPLATE.format(**weights)

    tree_json = json.dumps(merged_tree, indent=2)
    user_prompt = (
        f"Enrich and score this topic tree:\n\n{tree_json}"
    )

    for attempt in range(max_retries):
        try:
            logger.info("Phase 3 enrich (attempt %d)", attempt + 1)

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            text = response.content[0].text
            enriched = json.loads(text)

            if isinstance(enriched, dict) and "topics" in enriched:
                enriched = enriched["topics"]

            logger.info("Phase 3 complete")
            return enriched

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Phase 3 malformed JSON (attempt %d): %s", attempt + 1, e)
        except anthropic.APIError as e:
            logger.warning("Phase 3 API error (attempt %d): %s", attempt + 1, e)

    logger.error("Phase 3 failed after %d retries, returning unscored tree", max_retries)
    return merged_tree
