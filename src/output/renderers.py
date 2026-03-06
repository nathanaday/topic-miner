import json


def render_markdown(output: dict) -> str:
    lines = []
    meta = output["metadata"]
    lines.append(f"# {meta['course_name']} -- Topic Map")
    lines.append(f"**Semester:** {meta['semester']}")
    lines.append(f"**Generated:** {meta['generated_at']}")
    lines.append("")

    stats = meta["stats"]
    lines.append(
        f"**{stats['total_concepts']} concepts, "
        f"{stats['total_subtopics']} subtopics, "
        f"{stats['total_learning_outcomes']} learning outcomes**"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    def render_node(node, depth=0):
        indent = "  " * depth
        band = node.get("priority_band", "")
        score = node.get("priority_score", "?")
        band_marker = {
            "critical": "[!!!]",
            "important": "[!!]",
            "moderate": "[!]",
            "low": "",
        }.get(band, "")

        lines.append(f"{indent}- **{node['topic']}** (score: {score}) {band_marker}")

        if node.get("description"):
            lines.append(f"{indent}  {node['description']}")

        if node.get("study_note"):
            lines.append(f"{indent}  *Focus:* {node['study_note']}")

        if node.get("mastery_checklist"):
            for item in node["mastery_checklist"]:
                lines.append(f"{indent}  - [ ] {item}")

        refs = node.get("source_refs", [])
        if refs:
            ref_strs = []
            for ref in refs:
                ref_strs.append(
                    f"{ref['filename']}:{ref['lines'][0]}-{ref['lines'][1]}"
                )
            lines.append(f"{indent}  Sources: {', '.join(ref_strs)}")

        for child in node.get("subtopics", []):
            render_node(child, depth + 1)

    for topic in output["topics"]:
        render_node(topic)
        lines.append("")

    return "\n".join(lines)


def render_checklist(output: dict) -> str:
    lines = []
    meta = output["metadata"]
    lines.append(f"# {meta['course_name']} -- Study Checklist")
    lines.append("")

    outcomes = []

    def collect_outcomes(node, path=""):
        current_path = f"{path} > {node['topic']}" if path else node["topic"]
        if node["level"] == "learning_outcome" or not node.get("subtopics"):
            outcomes.append({
                "path": current_path,
                "topic": node["topic"],
                "description": node.get("description", ""),
                "score": node.get("priority_score", 0),
                "band": node.get("priority_band", "low"),
            })
        for child in node.get("subtopics", []):
            collect_outcomes(child, current_path)

    for topic in output["topics"]:
        collect_outcomes(topic)

    outcomes.sort(key=lambda x: x["score"], reverse=True)

    for item in outcomes:
        lines.append(f"- [ ] [{item['score']}] {item['path']}")
        if item["description"]:
            lines.append(f"      {item['description']}")

    return "\n".join(lines)
