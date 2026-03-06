import json
import logging

import anthropic

from .map_phase import strip_markdown_fences

from .prompts import MERGE_PROMPT

logger = logging.getLogger(__name__)


def merge_two_trees(tree_a: list[dict], tree_b: list[dict],
                    client: anthropic.Anthropic, model: str,
                    max_tokens: int, max_retries: int = 3) -> list[dict]:
    tree_a_json = json.dumps(tree_a, indent=2)
    tree_b_json = json.dumps(tree_b, indent=2)

    user_prompt = (
        f"Merge these two topic trees into a single unified tree.\n\n"
        f"TREE A:\n{tree_a_json}\n\n"
        f"TREE B:\n{tree_b_json}"
    )

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=MERGE_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            text = strip_markdown_fences(response.content[0].text)
            merged = json.loads(text)

            if isinstance(merged, dict) and "topics" in merged:
                merged = merged["topics"]

            return merged

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Phase 2 merge malformed JSON (attempt %d): %s", attempt + 1, e)
        except anthropic.APIError as e:
            logger.warning("Phase 2 merge API error (attempt %d): %s", attempt + 1, e)

    logger.error("Phase 2 merge failed after %d retries, concatenating trees", max_retries)
    return tree_a + tree_b


def pairwise_reduce(topic_trees: list[list[dict]], client: anthropic.Anthropic,
                    model: str, max_tokens: int) -> list[dict]:
    if len(topic_trees) == 0:
        return []
    if len(topic_trees) == 1:
        return topic_trees[0]

    current_round = topic_trees

    round_num = 0
    while len(current_round) > 1:
        round_num += 1
        logger.info("  Round %d: %d trees remaining", round_num, len(current_round))
        next_round = []

        for i in range(0, len(current_round), 2):
            if i + 1 < len(current_round):
                merged = merge_two_trees(
                    current_round[i], current_round[i + 1],
                    client, model, max_tokens
                )
                next_round.append(merged)
            else:
                next_round.append(current_round[i])

        current_round = next_round

    logger.info("Phase 2 complete")
    return current_round[0]


def run_reduce_phase(map_results: list[dict], config: dict) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_reduce"]

    client = anthropic.Anthropic(api_key=config["api_key"])

    topic_trees = []
    for result in map_results:
        topics = result.get("topics", [])
        if topics:
            topic_trees.append(topics)

    return pairwise_reduce(topic_trees, client, model, max_tokens)
