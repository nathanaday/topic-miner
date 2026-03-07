"""Topic Map API -- serves and mutates topic_map.json files managed via projects."""

import json
import os
import shutil
import subprocess
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
# Paths
# ---------------------------------------------------------------------------

APP_FILES_DIR = Path(__file__).resolve().parent.parent / "app-files"
SETTINGS_PATH = APP_FILES_DIR / "settings.json"

# ---------------------------------------------------------------------------
# In-memory store (active project's topic map)
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


def _unload():
    global _topic_map, _map_path
    _topic_map = {}
    _map_path = ""
    _by_id.clear()
    _by_name.clear()


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
# Study session helpers
# ---------------------------------------------------------------------------

def _collect_learning_outcomes(node: dict) -> list[str]:
    outcomes = list(node.get("mastery_checklist") or [])
    for child in node.get("subtopics", []):
        outcomes.extend(_collect_learning_outcomes(child))
    return outcomes


def _collect_source_refs(node: dict) -> list[dict]:
    refs = list(node.get("source_refs") or [])
    for child in node.get("subtopics", []):
        refs.extend(_collect_source_refs(child))
    seen = set()
    unique = []
    for ref in refs:
        doc_id = ref.get("doc_id", "")
        if doc_id not in seen:
            seen.add(doc_id)
            unique.append(ref)
    return unique


def _resolve_source_path(source_base_path: str, ref: dict) -> str:
    return str(Path(source_base_path) / ref.get("material_type", "") / ref.get("filename", ""))


_STUDY_SESSION_TEMPLATE = """\
# Study Session: {topic_name}

---

## Tutor Persona

You are a patient, encouraging study tutor. Your job is to help the student
deeply understand the topic below through active conversation, not passive
explanation.

### Core Approach

Your primary method is Socratic questioning. You do NOT give lectures or
lengthy explanations unprompted. Instead, you lead the student to demonstrate
and build understanding through their own words. Your goal is to surface what
the student knows, identify gaps, and guide them to fill those gaps
themselves.

### Conversation Flow

Follow this general rhythm throughout the session:

1. Begin by asking the student what they already know about the topic.
   Something like: "Before we dive in, tell me what you already know about
   {topic_name}. Even a rough sense is fine."

2. Based on their response, identify which learning outcomes they seem
   comfortable with and which need work. Do not announce this assessment
   out loud. Use it to guide your questions.

3. Work through the learning outcomes by asking the student to explain
   concepts in their own words. Use prompts like:
   - "Walk me through how [process] works, step by step."
   - "Describe in your own words what happens during [stage]."
   - "If you had to explain [concept] to someone who has never taken this
     class, what would you say?"
   - "Why does [thing] happen? What would go wrong if it didn't?"
   - "How does [concept A] connect to [concept B]?"

4. When the student gives a correct explanation, affirm it briefly and move
   on. When they are partially correct, ask a follow-up that targets the
   gap: "You're on the right track with [correct part]. Now, what happens
   next?" or "That's close -- what role does [missing element] play in that
   step?"

5. When the student is stuck, do not immediately explain. Instead, give a
   small hint or reframe the question. Only provide a direct explanation as
   a last resort, and keep it brief. Then immediately follow up with a
   question that checks whether they understood.

6. Periodically check in on the student's confidence. Ask things like:
   "How are you feeling about this so far?" or "Do you want to keep going
   on this area or move to something new?"

### Practice Questions
{practice_section}
### Tone

Be warm but not patronizing. Treat the student as capable. Avoid saying
things like "Great job!" after every response -- instead, show that you
are listening by engaging substantively with what they said. If they
make an error, treat it as interesting rather than wrong: "That's a common
way to think about it, but there's a catch -- what happens when..."

### What NOT To Do

- Do not dump a wall of text explaining the entire topic.
- Do not present all learning outcomes as a checklist to work through.
- Do not ask yes/no questions when you can ask open-ended ones.
- Do not offer practice questions if none exist in the source materials.
- Do not move on from a concept until the student has articulated
  understanding of it themselves.

---

## Topic

**{topic_name}**

{description}
{study_note_section}
## Learning Outcomes

The student should be able to:

{learning_outcomes}

---

## Source Materials

Read the following files before beginning the session. These are the
authoritative references for this topic. Base all of your questions and
any explanations on the content in these documents.

{source_files}

---

## Begin

Read all source materials listed above, then open the session by greeting
the student and asking what they already know about {topic_name}. Do not
summarize the topic yourself. Start with a question.
"""


def _render_study_session(
    topic_name: str,
    description: str,
    study_note: str,
    outcomes: list[str],
    source_entries: list[tuple[str, str]],
    has_exam: bool,
    has_homework: bool,
) -> str:
    outcome_lines = "\n".join(f"- {o}" for o in outcomes) if outcomes else "- (No specific outcomes listed)"

    source_lines = []
    for path, material_type in source_entries:
        source_lines.append(f"- `{path}`\n  {material_type}")
    source_text = "\n\n".join(source_lines) if source_lines else "- (No source files referenced)"

    study_note_section = f"\n{study_note}\n\n" if study_note else "\n"

    practice_parts = []
    if has_exam or has_homework:
        practice_parts.append(
            "Exam and homework questions should be offered, NOT forced. After the student\n"
            "has worked through a concept and demonstrated reasonable understanding,\n"
            "offer a practice question if one is available:\n"
        )
        if has_exam:
            practice_parts.append('- "There\'s an exam-style question on this in the materials. Want to try it?"')
        if has_homework:
            practice_parts.append('- "I have a homework problem that tests exactly this. Want to give it a shot?"')
        practice_parts.append(
            "\nIf the student accepts, present the question, let them answer, then discuss\n"
            "their response. If they decline, move on.\n\n"
            "IMPORTANT: Only offer exam or homework questions if they actually exist in\n"
            "the source materials listed below. Do not fabricate practice questions.\n"
        )
        practice_parts.append(f"- Exam questions available: {'YES' if has_exam else 'NO'}")
        practice_parts.append(f"- Homework questions available: {'YES' if has_homework else 'NO'}")
    else:
        practice_parts.append(
            "No exam or homework questions are available in the source materials for\n"
            "this topic. Do not fabricate practice questions."
        )
    practice_section = "\n" + "\n".join(practice_parts) + "\n"

    return _STUDY_SESSION_TEMPLATE.format(
        topic_name=topic_name,
        description=description or "(No description available)",
        study_note_section=study_note_section,
        learning_outcomes=outcome_lines,
        source_files=source_text,
        practice_section=practice_section,
    )


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

_DEFAULT_SETTINGS = {"version": 1, "active_project_id": None, "projects": []}


def _read_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return dict(_DEFAULT_SETTINGS, projects=[])
    with open(SETTINGS_PATH) as f:
        return json.load(f)


def _write_settings(settings: dict):
    APP_FILES_DIR.mkdir(parents=True, exist_ok=True)
    tmp = str(SETTINGS_PATH) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(settings, f, indent=2)
    shutil.move(tmp, str(SETTINGS_PATH))


def _find_project(settings: dict, project_id: str) -> dict | None:
    return next((p for p in settings["projects"] if p["id"] == project_id), None)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def _startup():
    APP_FILES_DIR.mkdir(parents=True, exist_ok=True)
    settings = _read_settings()
    active_id = settings.get("active_project_id")
    if active_id:
        project = _find_project(settings, active_id)
        if project:
            path = str(APP_FILES_DIR / project["topic_map_filename"])
            if os.path.exists(path):
                _load(path)


# ---------------------------------------------------------------------------
# Project endpoints
# ---------------------------------------------------------------------------

@app.get("/api/projects")
def list_projects():
    settings = _read_settings()
    return {
        "active_project_id": settings.get("active_project_id"),
        "projects": settings.get("projects", []),
    }


@app.post("/api/projects")
async def create_project(
    name: str = Form(...),
    source_base_path: str = Form(""),
    topic_map: UploadFile = File(...),
):
    content = await topic_map.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON file")
    if "topics" not in data:
        raise HTTPException(400, "JSON must contain a 'topics' key")

    project_id = str(_uuid.uuid4())
    filename = f"{project_id}.json"
    dest = APP_FILES_DIR / filename

    with open(dest, "w") as f:
        json.dump(data, f, indent=2)

    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": project_id,
        "name": name,
        "created_at": now,
        "last_opened_at": now,
        "source_base_path": source_base_path,
        "topic_map_filename": filename,
    }

    settings = _read_settings()
    settings["projects"].append(project)
    settings["active_project_id"] = project_id
    _write_settings(settings)

    _load(str(dest))
    return project


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, body: dict):
    settings = _read_settings()
    project = _find_project(settings, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    if "name" in body:
        project["name"] = body["name"]
    if "source_base_path" in body:
        project["source_base_path"] = body["source_base_path"]

    _write_settings(settings)
    return project


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    settings = _read_settings()
    project = _find_project(settings, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Remove topic map file
    map_file = APP_FILES_DIR / project["topic_map_filename"]
    if map_file.exists():
        map_file.unlink()

    settings["projects"] = [p for p in settings["projects"] if p["id"] != project_id]

    if settings["active_project_id"] == project_id:
        if settings["projects"]:
            # Switch to most recently opened
            most_recent = max(settings["projects"], key=lambda p: p.get("last_opened_at", ""))
            settings["active_project_id"] = most_recent["id"]
            _write_settings(settings)
            _load(str(APP_FILES_DIR / most_recent["topic_map_filename"]))
        else:
            settings["active_project_id"] = None
            _write_settings(settings)
            _unload()
    else:
        _write_settings(settings)

    return {"status": "deleted"}


@app.post("/api/projects/{project_id}/activate")
def activate_project(project_id: str):
    settings = _read_settings()
    project = _find_project(settings, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    project["last_opened_at"] = datetime.now(timezone.utc).isoformat()
    settings["active_project_id"] = project_id
    _write_settings(settings)

    path = str(APP_FILES_DIR / project["topic_map_filename"])
    if not os.path.exists(path):
        raise HTTPException(404, "Topic map file not found")
    _load(path)
    return project


@app.get("/api/projects/{project_id}/export")
def export_project(project_id: str):
    settings = _read_settings()
    project = _find_project(settings, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    path = APP_FILES_DIR / project["topic_map_filename"]
    if not path.exists():
        raise HTTPException(404, "Topic map file not found")

    with open(path) as f:
        content = f.read()

    safe_name = project["name"].replace('"', "").replace(" ", "_")
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_backup.json"'},
    )


# ---------------------------------------------------------------------------
# Topic map endpoints
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


# ---------------------------------------------------------------------------
# Study session endpoints
# ---------------------------------------------------------------------------

@app.post("/api/topics/{identifier:path}/study-session")
def generate_study_session(identifier: str):
    node = _find(identifier)
    if not node:
        raise HTTPException(404, "Topic not found")

    settings = _read_settings()
    active_id = settings.get("active_project_id")
    if not active_id:
        raise HTTPException(400, "No active project")
    project = _find_project(settings, active_id)
    if not project:
        raise HTTPException(400, "Active project not found")

    source_base_path = project.get("source_base_path", "")
    if not source_base_path:
        raise HTTPException(400, "Project has no source_base_path configured. Edit the project to set it.")
    if not Path(source_base_path).is_dir():
        raise HTTPException(400, f"Source directory not found: {source_base_path}")

    outcomes = _collect_learning_outcomes(node)
    refs = _collect_source_refs(node)

    source_entries = [
        (_resolve_source_path(source_base_path, ref), ref.get("material_type", ""))
        for ref in refs
    ]

    has_exam = any(ref.get("material_type") == "exam" for ref in refs)
    has_homework = any(ref.get("material_type") == "homework" for ref in refs)

    markdown = _render_study_session(
        topic_name=node.get("topic", ""),
        description=node.get("description", ""),
        study_note=node.get("study_note", ""),
        outcomes=outcomes,
        source_entries=source_entries,
        has_exam=has_exam,
        has_homework=has_homework,
    )

    file_path = str(Path(source_base_path) / "study-session.md")
    with open(file_path, "w") as f:
        f.write(markdown)

    return {"markdown": markdown, "file_path": file_path, "topic_name": node.get("topic", "")}


class LaunchClaudeRequest(BaseModel):
    file_path: str


@app.post("/api/launch-claude")
def launch_claude(body: LaunchClaudeRequest):
    if not shutil.which("claude"):
        raise HTTPException(400, "Claude CLI not found on PATH. Install it from https://docs.anthropic.com/en/docs/claude-code")

    prompt = f"Read the file at {body.file_path} and follow its instructions to begin a study session with me."
    subprocess.Popen([
        "osascript", "-e",
        f'tell application "Terminal" to do script "claude \'{prompt}\'"',
    ])
    return {"status": "launched"}
