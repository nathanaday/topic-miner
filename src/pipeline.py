import asyncio
import json
import logging
from datetime import datetime, timezone

from .config import load_config
from .ingest import ingest
from .map_phase import run_map_phase
from .reduce_phase import run_reduce_phase
from .enrich_phase import run_enrich_phase
from .output.renderers import render_markdown, render_checklist

import anthropic

logger = logging.getLogger(__name__)


def build_document_registry(documents: list[dict]) -> list[dict]:
    seen = {}
    registry = []
    for doc in documents:
        base_id = doc["base_doc_id"]
        if base_id not in seen:
            seen[base_id] = {
                "doc_id": base_id,
                "filename": doc["filename"],
                "material_type": doc["material_type"],
                "total_lines": doc["total_lines"],
                "chunks": doc["num_chunks"],
            }
    return list(seen.values())


def count_nodes(topics: list[dict]) -> dict:
    stats = {"concepts": 0, "subtopics": 0, "learning_outcomes": 0, "total": 0}

    def walk(node):
        stats["total"] += 1
        level = node.get("level", "")
        if level == "concept":
            stats["concepts"] += 1
        elif level == "subtopic":
            stats["subtopics"] += 1
        elif level == "learning_outcome":
            stats["learning_outcomes"] += 1
        for child in node.get("subtopics", []):
            walk(child)

    for topic in topics:
        walk(topic)
    return stats


def run_pipeline(input_dir: str, config_path: str = "material_config.yaml",
                 output_path: str = "topic_map.json",
                 render: list[str] | None = None,
                 from_phase: int = 0):
    config = load_config(config_path)
    client = anthropic.Anthropic(api_key=config["api_key"])

    documents = None
    map_results = None
    merged_tree = None

    if from_phase <= 0:
        # Phase 0: Ingest
        logger.info("=== Phase 0: Ingestion ===")
        documents = ingest(input_dir, config, client)
        logger.info("Ingested %d document chunks from %s", len(documents), input_dir)

        for doc in documents:
            logger.info("  [%s] %s (%s)", doc["doc_id"], doc["filename"], doc["material_type"])

    if from_phase <= 1:
        # Phase 1: Map
        if documents is None:
            logger.info("=== Phase 0: Ingestion ===")
            documents = ingest(input_dir, config, client)
            logger.info("Ingested %d document chunks from %s", len(documents), input_dir)

        logger.info("=== Phase 1: Map (per-document extraction) ===")
        map_results = asyncio.run(run_map_phase(documents, config))
        logger.info("Extracted topic trees from %d documents", len(map_results))

        with open("phase1_results.json", "w") as f:
            json.dump(map_results, f, indent=2)
        logger.info("Saved Phase 1 results to phase1_results.json")

    if from_phase <= 2:
        # Phase 2: Reduce
        if map_results is None:
            logger.info("Loading Phase 1 results from phase1_results.json")
            with open("phase1_results.json", "r") as f:
                map_results = json.load(f)

        logger.info("=== Phase 2: Reduce (pairwise merge) ===")
        merged_tree = run_reduce_phase(map_results, config)
        logger.info("Merged into unified tree")

        with open("phase2_results.json", "w") as f:
            json.dump(merged_tree, f, indent=2)
        logger.info("Saved Phase 2 results to phase2_results.json")

    # Phase 3: Enrich
    if merged_tree is None:
        logger.info("Loading Phase 2 results from phase2_results.json")
        with open("phase2_results.json", "r") as f:
            merged_tree = json.load(f)

    logger.info("=== Phase 3: Enrich & Prioritize ===")
    enriched_tree = run_enrich_phase(merged_tree, config)

    # Build final output
    if documents is None:
        documents = ingest(input_dir, config, client)

    doc_registry = build_document_registry(documents)
    node_stats = count_nodes(enriched_tree)

    final_output = {
        "metadata": {
            "course_name": config["course_name"],
            "semester": config["semester"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "1.0.0",
            "document_registry": doc_registry,
            "stats": {
                "total_documents": len(doc_registry),
                "total_concepts": node_stats["concepts"],
                "total_subtopics": node_stats["subtopics"],
                "total_learning_outcomes": node_stats["learning_outcomes"],
                "total_nodes": node_stats["total"],
            },
        },
        "topics": enriched_tree,
    }

    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2)
    logger.info("Saved final output to %s", output_path)

    # Optional renderers
    if render:
        if "markdown" in render:
            md_path = output_path.replace(".json", ".md")
            with open(md_path, "w") as f:
                f.write(render_markdown(final_output))
            logger.info("Rendered markdown to %s", md_path)

        if "checklist" in render:
            cl_path = output_path.replace(".json", "_checklist.md")
            with open(cl_path, "w") as f:
                f.write(render_checklist(final_output))
            logger.info("Rendered checklist to %s", cl_path)

    return final_output
