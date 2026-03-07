"""
Utility to detect duplicate topic IDs in a topic map JSON file.
Recursively walks the nested topic structure and reports any IDs that appear more than once.
"""

import json
import sys
from collections import defaultdict


def collect_ids(topics, id_locations, ancestor_path=None):
    """Recursively collect all topic IDs with their ancestor hierarchy paths."""
    if ancestor_path is None:
        ancestor_path = []
    for topic in topics:
        topic_id = topic.get("id")
        topic_name = topic.get("topic", "(no name)")
        description = topic.get("description", "")
        current_path = ancestor_path + [topic_name]
        if topic_id:
            id_locations[topic_id].append({
                "name": topic_name,
                "description": description,
                "path": current_path,
            })
        subtopics = topic.get("subtopics", [])
        if subtopics:
            collect_ids(subtopics, id_locations, current_path)


def detect_duplicates(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    topics = data.get("topics", [])
    id_locations = defaultdict(list)
    collect_ids(topics, id_locations)

    total_ids = sum(len(v) for v in id_locations.values())
    unique_ids = len(id_locations)
    duplicates = {k: v for k, v in id_locations.items() if len(v) > 1}

    print(f"Total topic IDs found: {total_ids}")
    print(f"Unique topic IDs: {unique_ids}")
    print(f"Duplicate IDs: {len(duplicates)}")
    print()

    if duplicates:
        print("=== DUPLICATES ===")
        for topic_id, entries in sorted(duplicates.items()):
            name = entries[0]["name"]
            desc = entries[0]["description"]
            print(f"\n  ID: {topic_id} (appears {len(entries)} times)")
            print(f"  Topic: {name}")
            if desc:
                print(f"  Description: {desc}")
            paths_seen = []
            for entry in entries:
                path_str = " > ".join(entry["path"])
                paths_seen.append(path_str)
            unique_paths = set(paths_seen)
            if len(unique_paths) == 1:
                print(f"  [All {len(entries)} occurrences share the same path]")
                print(f"    - {paths_seen[0]}")
            else:
                for path_str in paths_seen:
                    print(f"    - {path_str}")
    else:
        print("No duplicate topic IDs found.")

    return duplicates


if __name__ == "__main__":
    if len(sys.argv) < 2:
        path = "/Users/nathanaday/SoftwareProjects/topic-miner/_previous_results/week1-week8/topic_map.json"
        print(f"No path provided, using default:\n  {path}\n")
    else:
        path = sys.argv[1]

    detect_duplicates(path)
