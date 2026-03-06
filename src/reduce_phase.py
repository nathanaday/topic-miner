import json
import logging
import time

import anthropic

from .map_phase import strip_markdown_fences

from .prompts import MERGE_PROMPT, CONSOLIDATE_PROMPT

logger = logging.getLogger(__name__)

API_TIMEOUT = 300.0
TOKEN_LIMIT = 195_000  # stay under the 200k API limit


def estimate_tokens(text: str) -> int:
    return len(text) // 4


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

    est_tokens = estimate_tokens(MERGE_PROMPT + user_prompt)
    if est_tokens > TOKEN_LIMIT:
        logger.warning("  %s prompt too large (~%dk tokens), skipping merge and concatenating",
                        label, est_tokens // 1000)
        return tree_a + tree_b

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


def consolidate_tree(tree: list[dict], client: anthropic.Anthropic,
                     model: str, max_tokens: int,
                     max_retries: int = 3) -> list[dict]:
    concept_summary = []
    for node in tree:
        concept_summary.append({
            "topic": node["topic"],
            "description": node.get("description", ""),
            "num_children": len(node.get("subtopics", [])),
        })

    summary_json = json.dumps(concept_summary, indent=2)
    user_prompt = (
        f"Here are {len(concept_summary)} top-level concepts from a course topic tree. "
        f"Produce a consolidation plan.\n\n{summary_json}"
    )

    for attempt in range(max_retries):
        try:
            logger.info("  Consolidation pass (attempt %d)...", attempt + 1)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=CONSOLIDATE_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=API_TIMEOUT,
            )

            text = strip_markdown_fences(response.content[0].text)
            plan = json.loads(text)
            break
        except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
            logger.warning("  Consolidation bad response (attempt %d/%d): %s", attempt + 1, max_retries, e)
    else:
        logger.error("  Consolidation failed, returning tree as-is")
        return tree

    # Index the original tree by topic name
    topic_index = {}
    for node in tree:
        name = node["topic"]
        if name in topic_index:
            # Duplicate name -- merge subtrees
            existing = topic_index[name]
            existing["subtopics"] = existing.get("subtopics", []) + node.get("subtopics", [])
            existing["source_refs"] = existing.get("source_refs", []) + node.get("source_refs", [])
            existing["importance_signals"] = existing.get("importance_signals", []) + node.get("importance_signals", [])
        else:
            topic_index[name] = node

    # Apply the plan
    keeps = {}
    merges = []
    demotes = []

    for action in plan:
        input_topic = action["input_topic"]
        if input_topic not in topic_index:
            continue

        if action["action"] == "keep":
            new_name = action.get("new_name") or input_topic
            node = topic_index[input_topic]
            node["topic"] = new_name
            keeps[input_topic] = node
        elif action["action"] == "merge":
            merges.append((input_topic, action["target"]))
        elif action["action"] == "demote":
            demotes.append((input_topic, action["target"]))

    # Process merges: fold source into target
    for source_name, target_name in merges:
        source = topic_index.get(source_name)
        # Find target in keeps, or in topic_index as fallback
        target = keeps.get(target_name) or topic_index.get(target_name)
        if source and target:
            target["subtopics"] = target.get("subtopics", []) + source.get("subtopics", [])
            target["source_refs"] = target.get("source_refs", []) + source.get("source_refs", [])
            target["importance_signals"] = target.get("importance_signals", []) + source.get("importance_signals", [])
            if target["topic"] not in keeps:
                keeps[target["topic"]] = target

    # Process demotions: move source under target as a subtopic
    for source_name, target_name in demotes:
        source = topic_index.get(source_name)
        target = keeps.get(target_name) or topic_index.get(target_name)
        if source and target:
            source["level"] = "subtopic"
            target.setdefault("subtopics", []).append(source)
            if target["topic"] not in keeps:
                keeps[target["topic"]] = target

    result = list(keeps.values())
    logger.info("  Consolidated: %d -> %d top-level concepts", len(tree), len(result))
    return result


def run_reduce_phase(map_results: list[dict], config: dict) -> list[dict]:
    model = config["llm"]["model"]
    max_tokens = config["llm"]["max_tokens_reduce"]

    client = anthropic.Anthropic(api_key=config["api_key"])

    topic_trees = []
    for result in map_results:
        topics = result.get("topics", [])
        if topics:
            topic_trees.append(topics)

    merged = pairwise_reduce(topic_trees, client, model, max_tokens)

    # Post-merge consolidation if tree has too many top-level concepts
    if len(merged) > 40:
        logger.info("  %d top-level concepts detected, running consolidation...", len(merged))
        merged = consolidate_tree(merged, client, model, max_tokens)

    return merged
