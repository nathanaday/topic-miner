#!/usr/bin/env python3
import argparse
import logging

from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Course Topic Mapper -- map-reduce LLM pipeline for topic extraction"
    )
    parser.add_argument(
        "input_dir",
        help="Path to directory containing course materials",
    )
    parser.add_argument(
        "--config", "-c",
        default="material_config.yaml",
        help="Path to material_config.yaml (default: material_config.yaml)",
    )
    parser.add_argument(
        "--output", "-o",
        default="topic_map.json",
        help="Output JSON file path (default: topic_map.json)",
    )
    parser.add_argument(
        "--render", "-r",
        nargs="+",
        choices=["markdown", "checklist"],
        help="Optional rendered outputs: markdown, checklist",
    )
    parser.add_argument(
        "--from-phase",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="Resume from a specific phase (loads intermediate results from disk)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    run_pipeline(
        input_dir=args.input_dir,
        config_path=args.config,
        output_path=args.output,
        render=args.render,
        from_phase=args.from_phase,
    )


if __name__ == "__main__":
    main()
