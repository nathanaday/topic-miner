import base64
import glob
import json
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv(Path(__file__).parent / ".env")

PROMPT = """Convert this PDF to well-structured Markdown. This is a textbook chapter excerpt that will be processed downstream for topic pattern analysis, so completeness and structural accuracy matter more than visual formatting.

Guidelines:
- Preserve the full hierarchy of headings (chapter titles as #, sections as ##, subsections as ###, etc.)
- Capture ALL body text -- do not summarize or omit anything
- Preserve numbered/bulleted lists as-is
- Convert tables to Markdown tables where possible; if a table is too complex, represent it as clearly as you can
- For figures/diagrams, insert a placeholder like [Figure: <caption or brief description>] -- do not skip them silently
- Preserve bold/italic emphasis where it appears meaningful (e.g., key terms, definitions)
- Keep footnotes or endnotes as inline parentheticals or a notes section at the end
- Do not add any commentary, interpretation, or content that isn't in the source PDF
- If the PDF has page numbers, headers, or footers, omit those
- Output ONLY the Markdown content -- no preamble, no code fences, no explanation
"""


def load_config():
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        print("Error: config.json not found in script directory.")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    for key in ("source_files", "output_files", "max_limit"):
        if key not in config:
            print(f"Error: config.json missing required key '{key}'.")
            sys.exit(1)

    return config


def convert_pdf(client, pdf_path):
    pdf_bytes = pdf_path.read_bytes()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": PROMPT,
                    },
                ],
            }
        ],
    )

    return response.content[0].text


def main():
    config = load_config()
    source_pattern = config["source_files"]
    output_dir = Path(config["output_files"])
    max_limit = config["max_limit"]

    print("Loaded config.json")
    print(f"Source pattern: {source_pattern}")
    print(f"Output directory: {output_dir}")
    print(f"Max limit: {max_limit}")
    print()

    output_dir.mkdir(parents=True, exist_ok=True)

    matched = sorted(
        Path(p) for p in glob.glob(source_pattern) if p.lower().endswith(".pdf")
    )
    total_matched = len(matched)

    if total_matched == 0:
        print("Warning: No PDFs matched the source pattern.")
        return

    if total_matched > max_limit:
        skipped_count = total_matched - max_limit
        print(
            f"Found {total_matched} PDFs matching pattern "
            f"(capped at {max_limit}, skipping {skipped_count})"
        )
        matched = matched[:max_limit]
    else:
        print(f"Found {total_matched} PDFs matching pattern")

    print()

    client = anthropic.Anthropic()
    workers = config.get("workers", 5)

    successful = 0
    failed = []
    already_converted = 0
    to_process = len(matched)
    print_lock = threading.Lock()

    # Filter out already-converted files first
    pending = []
    for i, pdf_path in enumerate(matched, 1):
        label = f"[{i}/{to_process}]"
        md_name = pdf_path.stem + ".md"
        md_path = output_dir / md_name

        if md_path.exists():
            print(f"{label}  {pdf_path.name} -- skipped (already converted)")
            already_converted += 1
        else:
            pending.append((i, pdf_path, md_path, label))

    if pending:
        print(f"\nProcessing {len(pending)} PDFs with {workers} workers...\n")

    max_retries = 3

    def process_one(item):
        _, pdf_path, md_path, label = item
        for attempt in range(max_retries):
            try:
                markdown = convert_pdf(client, pdf_path)
                md_path.write_text(markdown, encoding="utf-8")
                with print_lock:
                    print(f"{label}  {pdf_path.name} -- success")
                return (pdf_path.name, None)
            except anthropic.RateLimitError:
                wait = 60 * (attempt + 1)
                with print_lock:
                    print(
                        f"{label}  {pdf_path.name} -- rate limited, "
                        f"retrying in {wait}s (attempt {attempt + 1}/{max_retries})"
                    )
                time.sleep(wait)
            except Exception as e:
                error_msg = str(e)
                with print_lock:
                    print(f"{label}  {pdf_path.name} -- FAILED ({error_msg})")
                return (pdf_path.name, error_msg)
        with print_lock:
            print(f"{label}  {pdf_path.name} -- FAILED (rate limited after {max_retries} retries)")
        return (pdf_path.name, "rate limited after all retries")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_one, item): item for item in pending}
        for future in as_completed(futures):
            name, error = future.result()
            if error:
                failed.append((name, error))
            else:
                successful += 1

    print()
    print("=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print(f"Total PDFs matched:   {total_matched}")
    if total_matched > max_limit:
        print(f"Limit applied:        {max_limit}")
    print(f"Already converted:    {already_converted}")
    print(f"Successful:           {successful}")
    print(f"Failed:               {len(failed)}")

    if failed:
        print()
        print("Failed files:")
        for name, reason in failed:
            print(f"  - {name}: {reason}")


if __name__ == "__main__":
    main()
