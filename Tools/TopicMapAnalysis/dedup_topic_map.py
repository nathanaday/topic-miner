"""
Procedural deduplication of topic map JSON files.

Handles two cases:
1. Exact clones (same ID, same parent path): merge fields sideways and keep one copy.
2. Structural duplicates (same ID, different paths): merge content from the
   shallower node into the deeper (more specific) node, then remove the shallow copy.

Usage:
    python3 dedup_topic_map.py [input_path] [output_path]
"""

import json
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dedup_list_of_dicts(items):
    """Deduplicate a list of dicts by their JSON serialization."""
    seen = set()
    result = []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _merge_scalar(values):
    """Pick the best scalar from a list of candidates: longest non-null string,
    or highest number, depending on type."""
    non_null = [v for v in values if v is not None]
    if not non_null:
        return None
    if isinstance(non_null[0], (int, float)):
        return max(non_null)
    if isinstance(non_null[0], str):
        return max(non_null, key=len)
    return non_null[0]


def _merge_topics(duplicates):
    """Merge a list of duplicate topic dicts (same ID, same parent) into one.
    Lists are combined and deduplicated. Scalars pick the best value.
    Subtopics are recursively merged after combining."""
    merged = {}

    # Start from the first copy as a base
    base = duplicates[0]
    merged["id"] = base["id"]
    merged["topic"] = base["topic"]
    merged["level"] = base["level"]

    # Merge scalar fields - pick best
    merged["description"] = _merge_scalar([d.get("description") for d in duplicates])
    merged["priority_score"] = _merge_scalar([d.get("priority_score") for d in duplicates])
    merged["priority_band"] = _merge_scalar([d.get("priority_band") for d in duplicates])
    merged["study_note"] = _merge_scalar([d.get("study_note") for d in duplicates])

    # Merge list fields - combine and deduplicate
    all_source_refs = []
    all_importance_signals = []
    all_mastery_items = []
    for d in duplicates:
        all_source_refs.extend(d.get("source_refs") or [])
        all_importance_signals.extend(d.get("importance_signals") or [])
        all_mastery_items.extend(d.get("mastery_checklist") or [])

    merged["source_refs"] = _dedup_list_of_dicts(all_source_refs)
    merged["importance_signals"] = _dedup_list_of_dicts(all_importance_signals)
    merged["mastery_checklist"] = _dedup_list_of_dicts(all_mastery_items) if all_mastery_items else None

    # Combine all subtopics from all duplicates, then dedup those recursively
    all_subtopics = []
    for d in duplicates:
        all_subtopics.extend(d.get("subtopics") or [])
    merged["subtopics"] = dedup_subtopics(all_subtopics)

    return merged


# ---------------------------------------------------------------------------
# Core dedup logic
# ---------------------------------------------------------------------------

def dedup_subtopics(subtopics):
    """Given a list of sibling subtopics, find duplicates by ID and merge them.
    Returns a new list with duplicates collapsed."""
    if not subtopics:
        return []

    # Group by ID, preserving order of first appearance
    groups = {}
    order = []
    for topic in subtopics:
        tid = topic.get("id")
        if tid not in groups:
            groups[tid] = []
            order.append(tid)
        groups[tid].append(topic)

    result = []
    for tid in order:
        copies = groups[tid]
        if len(copies) == 1:
            # No duplicate at this level, but recurse into children
            topic = copies[0]
            topic["subtopics"] = dedup_subtopics(topic.get("subtopics") or [])
            result.append(topic)
        else:
            # Merge duplicates sideways, then recurse into merged children
            merged = _merge_topics(copies)
            result.append(merged)

    return result


def collect_unique_topic_names(topics, names=None):
    """Recursively collect all (id, topic_name) pairs."""
    if names is None:
        names = set()
    for t in topics:
        tid = t.get("id", "")
        name = t.get("topic", "")
        names.add((tid, name))
        collect_unique_topic_names(t.get("subtopics") or [], names)
    return names


# ---------------------------------------------------------------------------
# Structural duplicate detection
# ---------------------------------------------------------------------------

def find_structural_duplicates(topics, ancestor_path=None, id_paths=None):
    """Walk the tree and collect the ancestor path for every topic ID.
    Returns a dict of {id: [list of path tuples]}."""
    if ancestor_path is None:
        ancestor_path = ()
    if id_paths is None:
        id_paths = defaultdict(list)

    for t in topics:
        tid = t.get("id")
        name = t.get("topic", "")
        current_path = ancestor_path + (name,)
        if tid:
            id_paths[tid].append(current_path)
        find_structural_duplicates(t.get("subtopics") or [], current_path, id_paths)

    return id_paths


# ---------------------------------------------------------------------------
# Structural duplicate resolution (different paths -> keep deepest)
# ---------------------------------------------------------------------------

def _index_nodes(topics, parent_subtopics_list=None, depth=0, ancestor_path=(), index=None):
    """Build an index of {id: [(depth, ancestor_path, node_ref, parent_list_ref)]}
    so we can locate and manipulate nodes in the tree."""
    if index is None:
        index = defaultdict(list)

    for t in topics:
        tid = t.get("id")
        name = t.get("topic", "")
        current_path = ancestor_path + (name,)
        if tid:
            index[tid].append({
                "depth": depth,
                "path": current_path,
                "node": t,
                "parent_list": topics,
            })
        _index_nodes(t.get("subtopics") or [], t.get("subtopics"), depth + 1, current_path, index)

    return index


def _merge_content_into(target, source):
    """Merge all content fields from source into target (in place).
    Same sideways merge logic as _merge_topics but operates on two nodes."""
    # Merge scalar fields - keep best (longest string / highest number)
    for field in ("description", "study_note"):
        src_val = source.get(field)
        tgt_val = target.get(field)
        if src_val and (not tgt_val or len(str(src_val)) > len(str(tgt_val))):
            target[field] = src_val

    for field in ("priority_score",):
        src_val = source.get(field)
        tgt_val = target.get(field)
        if src_val is not None and (tgt_val is None or src_val > tgt_val):
            target[field] = src_val

    for field in ("priority_band",):
        src_val = source.get(field)
        tgt_val = target.get(field)
        if src_val and (not tgt_val or len(src_val) > len(tgt_val)):
            target[field] = src_val

    # Merge list fields - combine and deduplicate
    for field in ("source_refs", "importance_signals"):
        combined = list(target.get(field) or []) + list(source.get(field) or [])
        target[field] = _dedup_list_of_dicts(combined)

    # mastery_checklist
    tgt_mc = target.get("mastery_checklist") or []
    src_mc = source.get("mastery_checklist") or []
    if tgt_mc or src_mc:
        combined = list(tgt_mc) + list(src_mc)
        target["mastery_checklist"] = _dedup_list_of_dicts(combined)

    # Merge subtopics from source into target
    src_subs = source.get("subtopics") or []
    if src_subs:
        tgt_subs = target.get("subtopics") or []
        tgt_subs.extend(src_subs)
        target["subtopics"] = dedup_subtopics(tgt_subs)


def resolve_structural_duplicates(topics):
    """Find IDs that appear at different depths, merge shallower into deeper,
    and remove the shallow copies. Returns the modified topics list."""
    index = _index_nodes(topics)

    # Find IDs with multiple distinct paths
    structural_dups = {}
    for tid, entries in index.items():
        unique_paths = set(e["path"] for e in entries)
        if len(unique_paths) > 1:
            structural_dups[tid] = entries

    if not structural_dups:
        return topics

    # Process each structural duplicate: merge shallow into deep, remove shallow
    # We need to collect removals and do them after to avoid modifying lists mid-iteration
    removals = []  # list of (parent_list_ref, node_ref) to remove

    for tid, entries in sorted(structural_dups.items()):
        # Sort by depth descending - deepest first
        by_depth = sorted(entries, key=lambda e: e["depth"], reverse=True)
        keeper = by_depth[0]  # deepest occurrence
        donors = by_depth[1:]  # shallower occurrences

        for donor in donors:
            # Only merge if this is truly a different path
            if donor["path"] != keeper["path"]:
                print(f"  Merging: {' > '.join(donor['path'])} (depth {donor['depth']})")
                print(f"    into:  {' > '.join(keeper['path'])} (depth {keeper['depth']})")
                _merge_content_into(keeper["node"], donor["node"])
                removals.append((donor["parent_list"], donor["node"]))

    # Remove shallow copies
    removed_count = 0
    for parent_list, node in removals:
        if node in parent_list:
            parent_list.remove(node)
            removed_count += 1

    print(f"  Structural duplicates resolved: {removed_count} shallow nodes removed")
    return topics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def dedup_topic_map(input_path, output_path):
    with open(input_path, "r") as f:
        data = json.load(f)

    topics = data.get("topics", [])

    # --- Pre-dedup stats ---
    pre_names = collect_unique_topic_names(topics)
    pre_id_paths = find_structural_duplicates(topics)
    pre_total = sum(len(v) for v in pre_id_paths.values())
    pre_unique = len(pre_id_paths)
    pre_dup_ids = {k: v for k, v in pre_id_paths.items() if len(v) > 1}

    # Separate structural duplicates (different paths) from exact clones (same path)
    structural_dups = {}
    same_path_dups = {}
    for tid, paths in pre_dup_ids.items():
        unique_paths = set(paths)
        if len(unique_paths) > 1:
            structural_dups[tid] = paths
        else:
            same_path_dups[tid] = paths

    print("=" * 60)
    print("PRE-DEDUP REPORT")
    print("=" * 60)
    print(f"Total topic nodes:        {pre_total}")
    print(f"Unique topic IDs:         {pre_unique}")
    print(f"Duplicate IDs (total):    {len(pre_dup_ids)}")
    print(f"  Exact clones (same path):       {len(same_path_dups)}")
    print(f"  Structural dups (diff paths):   {len(structural_dups)}")
    print()

    # --- Log structural duplicates ---
    if structural_dups:
        print("=" * 60)
        print("STRUCTURAL DUPLICATES (different paths - will merge deep)")
        print("=" * 60)
        for tid, paths in sorted(structural_dups.items()):
            unique_paths = sorted(set(paths))
            print(f"\n  ID: {tid} (appears {len(paths)} times across {len(unique_paths)} distinct paths)")
            for p in unique_paths:
                print(f"    - {' > '.join(p)}")
        print()

    # --- Phase 1: Collapse exact clones (same parent, same path) ---
    print("=" * 60)
    print("PHASE 1: Exact clone dedup (same path)")
    print("=" * 60)
    clean_topics = dedup_subtopics(topics)

    # --- Phase 2: Resolve structural duplicates (different paths -> keep deepest) ---
    print()
    print("=" * 60)
    print("PHASE 2: Structural dedup (merge shallow into deep)")
    print("=" * 60)
    clean_topics = resolve_structural_duplicates(clean_topics)

    data["topics"] = clean_topics

    # --- Post-dedup stats ---
    post_names = collect_unique_topic_names(clean_topics)
    post_id_paths = find_structural_duplicates(clean_topics)
    post_total = sum(len(v) for v in post_id_paths.values())
    post_unique = len(post_id_paths)
    post_dup_ids = {k: v for k, v in post_id_paths.items() if len(v) > 1}

    print("=" * 60)
    print("POST-DEDUP REPORT")
    print("=" * 60)
    print(f"Total topic nodes:        {post_total}")
    print(f"Unique topic IDs:         {post_unique}")
    print(f"Remaining duplicate IDs:  {len(post_dup_ids)}")
    print()

    # --- Validation: no unique topics lost ---
    lost = pre_names - post_names
    gained = post_names - pre_names
    if lost:
        print(f"WARNING: {len(lost)} unique topics LOST during dedup:")
        for tid, name in sorted(lost):
            print(f"  - {tid}: {name}")
    if gained:
        print(f"NOTE: {len(gained)} topics gained (should not happen):")
        for tid, name in sorted(gained):
            print(f"  - {tid}: {name}")
    if not lost and not gained:
        print("VALIDATION PASSED: All unique topics preserved, no topics lost.")

    nodes_removed = pre_total - post_total
    print(f"\nNodes removed: {nodes_removed}")
    print(f"  ({pre_total} -> {post_total})")

    # --- Update metadata stats ---
    if "metadata" in data and "stats" in data["metadata"]:
        stats = data["metadata"]["stats"]
        # Recount by level
        level_counts = defaultdict(int)
        def count_levels(topics_list):
            for t in topics_list:
                level_counts[t.get("level", "unknown")] += 1
                count_levels(t.get("subtopics") or [])
        count_levels(clean_topics)
        stats["total_nodes"] = post_total
        stats["total_concepts"] = level_counts.get("concept", 0)
        stats["total_subtopics"] = level_counts.get("subtopic", 0)
        stats["total_learning_outcomes"] = level_counts.get("learning_outcome", 0)

    # --- Write output ---
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nClean topic map written to: {output_path}")
    return data


if __name__ == "__main__":
    default_input = "/Users/nathanaday/SoftwareProjects/topic-miner/_previous_results/week1-week8/topic_map.json"
    default_output = "/Users/nathanaday/SoftwareProjects/topic-miner/_previous_results/week1-week8/topic_map_deduped.json"

    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output

    if input_path == default_input:
        print(f"Using default input:  {input_path}")
    if output_path == default_output:
        print(f"Using default output: {output_path}\n")

    dedup_topic_map(input_path, output_path)
