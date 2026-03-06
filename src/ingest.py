import hashlib
import os
from pathlib import Path

import anthropic

from .prompts import CLASSIFY_PROMPT


SUPPORTED_EXTENSIONS = {".md", ".txt", ".text", ".markdown"}


def file_doc_id(input_dir: str, filepath: str) -> str:
    rel_path = os.path.relpath(filepath, input_dir)
    short_hash = hashlib.md5(rel_path.encode()).hexdigest()[:8]
    return f"doc_{short_hash}"


def classify_file(filepath: str, directory_rules: dict, file_overrides: dict,
                  client: anthropic.Anthropic, model: str) -> str:
    filename = os.path.basename(filepath)
    if filename in file_overrides:
        return file_overrides[filename]

    rel_parts = Path(filepath).parts
    for dir_pattern, material_type in directory_rules.items():
        dir_name = dir_pattern.strip("/")
        if dir_name in rel_parts:
            return material_type

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = []
        for i, line in enumerate(f):
            if i >= 50:
                break
            lines.append(line)
    preview = "".join(lines)

    response = client.messages.create(
        model=model,
        max_tokens=20,
        temperature=0,
        messages=[{"role": "user", "content": f"Classify this document:\n\n{preview}"}],
        system=CLASSIFY_PROMPT,
    )
    classification = response.content[0].text.strip().lower()
    valid_types = {"lecture", "textbook", "homework", "exam", "discussion", "student"}
    if classification in valid_types:
        return classification
    return "student"


def discover_files(input_dir: str) -> list[str]:
    files = []
    for root, _, filenames in os.walk(input_dir):
        for fname in sorted(filenames):
            if Path(fname).suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, fname))
    return sorted(files)


def chunk_document(lines: list[str], chunk_size: int = 6000,
                   overlap: int = 200) -> list[tuple[int, int]]:
    if len(lines) <= chunk_size:
        return [(0, len(lines))]

    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + chunk_size, len(lines))
        chunks.append((start, end))
        if end >= len(lines):
            break
        start = end - overlap
    return chunks


def ingest(input_dir: str, config: dict, client: anthropic.Anthropic) -> list[dict]:
    directory_rules = config.get("directory_rules", {})
    file_overrides = config.get("file_overrides", {})
    model = config["llm"]["model"]

    filepaths = discover_files(input_dir)
    documents = []

    for filepath in filepaths:
        doc_id = file_doc_id(input_dir, filepath)

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.split("\n")
        material_type = classify_file(
            filepath, directory_rules, file_overrides, client, model
        )
        filename = os.path.basename(filepath)

        chunk_ranges = chunk_document(lines)
        num_chunks = len(chunk_ranges)

        for chunk_idx, (start, end) in enumerate(chunk_ranges):
            chunk_lines = lines[start:end]
            numbered_content = []
            for i, line in enumerate(chunk_lines):
                line_num = start + i + 1
                numbered_content.append(f"{line_num}: {line}")

            if num_chunks == 1:
                chunk_doc_id = doc_id
            else:
                chunk_doc_id = f"{doc_id}_chunk_{chunk_idx + 1:02d}"

            header = (
                f"[{chunk_doc_id}] {filename} (type: {material_type})\n"
                f"---\n"
            )

            documents.append({
                "doc_id": chunk_doc_id,
                "base_doc_id": doc_id,
                "filename": filename,
                "filepath": filepath,
                "material_type": material_type,
                "total_lines": len(lines),
                "chunk_index": chunk_idx,
                "num_chunks": num_chunks,
                "content": header + "\n".join(numbered_content),
            })

    return documents
