import json
import logging
import time

import anthropic

from .map_phase import strip_markdown_fences

from .prompts import MERGE_PROMPT

logger = logging.getLogger(__name__)

API_TIMEOUT = 300.0


def count_nodes(tree: list[dict]) -> int:
    total = 0
    for node in tree:
        total += 1
        total += count_nodes(node.get("subtopics", []))
    return total


def merge_two_trees(tree_a: list[dict], tree_b: list[dict],
                    client: anthropic.Anthropic, model: str,
                    max_tokens: int, label: str = "",
                    max_retries: int = 3) -> list[dict]:
    tree_a_json = json.dumps(tree_a, indent=2)
    tree_b_json = json.dumps(tree_b, indent=2)

    size_a = count_nodes(tree_a)
    size_b = count_nodes(tree_b)
    logger.info("  %s merging %d + %d nodes...", label, size_a, size_b)

    user_prompt = (
        f"Merge these two topic trees into a single unified tree.\n\n"
        f"TREE A:\n{tree_a_json}\n\n"
        f"TREE B:\n{tree_b_json}"
    )

    for attempt in range(max_retries):
        try:
            start = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=MERGE_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=API_TIMEOUT,
            )
            elapsed = time.time() - start

            if response.stop_reason == "max_tokens":
                logger.warning("  %s truncated after %.0fs -- merged tree too large", label, elapsed)
                logger.warning("  Falling back to concatenation for this pair")
                return tree_a + tree_b

            text = strip_markdown_fences(response.content[0].text)
            merged = json.loads(text)

            if isinstance(merged, dict) and "topics" in merged:
                merged = merged["topics"]

            merged_size = count_nodes(merged)
            logger.info("  %s done in %.0fs -> %d nodes", label, elapsed, merged_size)
            return merged

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("  %s bad JSON (attempt %d/%d): %s", label, attempt + 1, max_retries, e)
        except anthropic.APITimeoutError:
            logger.warning("  %s timed out after %.0fs (attempt %d/%d)", label, API_TIMEOUT, attempt + 1, max_retries)
        except anthropic.APIError as e:
            logger.warning("  %s API error (attempt %d/%d): %s", label, attempt + 1, max_retries, e)

    logger.error("  %s failed after %d retries, concatenating trees", label, max_retries)
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
        total_merges = len(current_round) // 2
        logger.info("  Round %d: %d trees -> %d merges", round_num, len(current_round), total_merges)
        next_round = []

        merge_num = 0
        for i in range(0, len(current_round), 2):
            if i + 1 < len(current_round):
                merge_num += 1
                label = f"[R{round_num} M{merge_num}/{total_merges}]"
                merged = merge_two_trees(
                    current_round[i], current_round[i + 1],
                    client, model, max_tokens, label=label
                )
                next_round.append(merged)
            else:
                logger.info("  [R%d] odd tree out, carrying forward", round_num)
                next_round.append(current_round[i])

        current_round = next_round

    logger.info("Phase 2 complete: %d nodes in final tree", count_nodes(current_round[0]))
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
