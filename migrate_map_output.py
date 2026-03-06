#!/usr/bin/env python3
"""One-time migration: rename map_output files from sequential IDs to hash-based IDs."""

import json
import os
import re

from src.ingest import file_doc_id

INPUT_DIR = "SampleCourse"
MAP_DIR = "map_output"

OLD_TO_REL_PATH = {
    "doc_001": "discussion/W4 Network Applications.md",
    "doc_002": "exam/midterm fall 2020.md",
    "doc_003": "homework/HW1.md",
    "doc_004": "lecture/EE 450 Lecture Video 01_13_2026_Captions_English (United States)-2.txt",
    "doc_005": "lecture/EE 450 Lecture Video 01_15_2026_Captions_English (United States).txt",
    "doc_006": "student/W1 - Networks Overview.md",
    "doc_007": "textbook/Kuros-1.1.md",
    "doc_008": "textbook/Kuros-1.2.md",
    "doc_009": "textbook/Kuros-1.3.md",
    "doc_010": "textbook/Kuros-1.4.md",
    "doc_011": "textbook/Kuros-1.5.md",
}

# Build old base ID -> new base ID mapping
id_map = {}
for old_base, rel_path in OLD_TO_REL_PATH.items():
    full_path = os.path.join(INPUT_DIR, rel_path)
    new_base = file_doc_id(INPUT_DIR, full_path)
    id_map[old_base] = new_base
    print(f"  {old_base} -> {new_base}  ({rel_path})")


def translate_id(old_id: str) -> str:
    for old_base, new_base in id_map.items():
        if old_id == old_base or old_id.startswith(old_base + "_"):
            suffix = old_id[len(old_base):]
            return new_base + suffix
    return old_id


def patch_json(data, old_id: str, new_id: str):
    """Recursively replace old doc ID references inside the JSON."""
    if isinstance(data, dict):
        return {k: patch_json(v, old_id, new_id) for k, v in data.items()}
    elif isinstance(data, list):
        return [patch_json(item, old_id, new_id) for item in data]
    elif isinstance(data, str) and old_id in data:
        return data.replace(old_id, new_id)
    return data


# Rename JSON files and patch contents
for fname in sorted(os.listdir(MAP_DIR)):
    if not fname.endswith(".json"):
        continue

    old_id = fname.replace(".json", "")
    new_id = translate_id(old_id)

    if old_id == new_id:
        continue

    old_path = os.path.join(MAP_DIR, fname)
    new_path = os.path.join(MAP_DIR, f"{new_id}.json")

    with open(old_path, "r") as f:
        data = json.load(f)

    data = patch_json(data, old_id, new_id)

    with open(new_path, "w") as f:
        json.dump(data, f, indent=2)

    os.remove(old_path)
    print(f"  {fname} -> {new_id}.json")

# Rewrite completed.txt
completed_path = os.path.join(MAP_DIR, "completed.txt")
with open(completed_path, "r") as f:
    old_entries = [line.strip() for line in f if line.strip()]

new_entries = [translate_id(entry) for entry in old_entries]

with open(completed_path, "w") as f:
    for entry in new_entries:
        f.write(entry + "\n")

print(f"\nMigrated {len(new_entries)} entries in completed.txt")
print("Done. You can now re-run the pipeline.")
