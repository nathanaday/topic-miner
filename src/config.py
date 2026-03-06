import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


def load_config(config_path: str = "material_config.yaml") -> dict:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in .env file")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    config["api_key"] = api_key
    return config
