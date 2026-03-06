"""Topic Map API -- serves and mutates the topic_map.json produced by the pipeline."""

import json
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Topic Map API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_topic_map: dict = {}
_map_path: str = ""
_by_id: dict[str, dict] = {}
_by_name: dict[str, list[dict]] = {}


def _build_index(nodes: list, parent_id: str | None = None, root_topic: str = ""):
    for node in nodes:
        nid = node.get("id", "")
        rt = root_topic or node.get("topic", "")
        node["_parent_id"] = parent_id
        node["_root_topic"] = rt
        _by_id[nid] = node
        _by_name.setdefault(node.get("topic", "").lower(), []).append(node)
        _build_index(node.get("subtopics", []), nid, rt)


def _load(path: str):
    global _topic_map, _map_path
    with open(path) as f:
        _topic_map = json.load(f)
    _map_path = path
    _by_id.clear()
    _by_name.clear()
    _build_index(_topic_map.get("topics", []))


def _save():
    tmp = _map_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(_topic_map, f, indent=2)
    shutil.move(tmp, _map_path)


def _find(identifier: str):
    """Lookup by ID first, then by exact topic name."""
    if identifier in _by_id:
        return _by_id[identifier]
    hits = _by_name.get(identifier.lower(), [])
    return hits[0] if hits else None


def _summary(node: dict) -> dict:
    return {
        "id": node.get("id"),
        "topic": node.get("topic"),
        "level": node.get("level"),
        "description": node.get("description"),
        "priority_score": node.get("priority_score"),
        "priority_band": node.get("priority_band"),
        "student_mastery_score": node.get("student_mastery_score"),
        "child_count": len(node.get("subtopics", [])),
    }


def _clean(node: dict) -> dict:
    """Return node dict without internal underscore keys."""
    return {k: v for k, v in node.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def _startup():
    path = os.environ.get(
        "TOPIC_MAP_PATH",
        str(Path(__file__).resolve().parent.parent.parent
            / "_previous_results" / "week1-week8" / "topic_map.json"),
    )
    _load(path)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/metadata")
def metadata():
    return _topic_map.get("metadata", {})


@app.get("/api/topics")
def list_topics():
    return [_summary(t) for t in _topic_map.get("topics", [])]


@app.get("/api/topics/{identifier:path}")
def get_topic(identifier: str):
    node = _find(identifier)
    if not node:
        raise HTTPException(404, "Topic not found")
    return _clean(node)


@app.get("/api/children/{identifier:path}")
def get_children(identifier: str):
    node = _find(identifier)
    if not node:
        raise HTTPException(404, "Topic not found")
    return [_summary(c) for c in node.get("subtopics", [])]


@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    q_lower = q.lower()
    results = []
    for nid, node in _by_id.items():
        if q_lower in node.get("topic", "").lower():
            results.append(_summary(node))
    return results


class MasteryUpdate(BaseModel):
    mastery_score: int


@app.put("/api/topics/{identifier:path}/mastery")
def update_mastery(identifier: str, body: MasteryUpdate):
    node = _find(identifier)
    if not node:
        raise HTTPException(404, "Topic not found")
    node["student_mastery_score"] = max(0, min(100, body.mastery_score))
    _save()
    return {"status": "updated", "id": node.get("id"),
            "mastery_score": node["student_mastery_score"]}


@app.get("/api/graph")
def graph():
    """Flattened nodes + links for D3 force layout."""
    nodes: list[dict] = []
    links: list[dict] = []
    seen: dict[str, int] = {}

    def walk(items, depth=0, parent_gid=None, root_topic=""):
        for item in items:
            original_id = item.get("id", "")
            rt = root_topic or item.get("topic", "")

            # Generate unique graph ID for D3
            count = seen.get(original_id, 0)
            seen[original_id] = count + 1
            gid = original_id if count == 0 else f"{original_id}__dup{count}"

            nodes.append({
                "id": gid,
                "original_id": original_id,
                "topic": item.get("topic", ""),
                "level": item.get("level", ""),
                "depth": depth,
                "description": item.get("description", ""),
                "priority_score": item.get("priority_score"),
                "priority_band": item.get("priority_band"),
                "student_mastery_score": item.get("student_mastery_score"),
                "parent_id": parent_gid,
                "root_topic": rt,
                "child_count": len(item.get("subtopics", [])),
            })
            if parent_gid:
                links.append({"source": parent_gid, "target": gid})
            walk(item.get("subtopics", []), depth + 1, gid, rt)

    walk(_topic_map.get("topics", []))
    return {"nodes": nodes, "links": links}


@app.get("/api/export")
def export_full():
    return _topic_map
