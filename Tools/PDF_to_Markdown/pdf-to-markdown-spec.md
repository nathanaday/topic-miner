# PDF-to-Markdown Batch Processor — Spec for Claude Code

## Overview

Build a Python script that batch-converts a directory of PDF files to Markdown using the Anthropic Claude API. Each PDF is a textbook chapter excerpt. The goal is complete text extraction with preserved section structure for downstream topic analysis.

## Requirements

### Core Behavior

- Read configuration from a `config.json` file in the script's directory
- Resolve the `source_files` glob pattern to find matching PDF files
- Enforce the `max_limit` cap — only process up to that many files per run
- For each PDF: read it, base64-encode it, send it to the Claude API as a document, and save the response as `<original_filename>.md` in the output directory
- Process files sequentially (no concurrency needed)
- Use the `anthropic` Python SDK (not raw HTTP)
- Use model `claude-sonnet-4-20250514`
- Read the API key from the `ANTHROPIC_API_KEY` environment variable (do not hardcode)

### Error Handling

- If a single PDF fails (API error, file read error, timeout, etc.), log the error with the filename and reason, then continue to the next file
- Do NOT stop the batch on individual failures

### Output

- Each `.md` file should be named to match the source PDF (e.g., `chapter_03.pdf` → `chapter_03.md`)
- Print a summary report at the end:
  - Total files found
  - Successful conversions
  - Failed conversions (with filenames and error reasons)

### Configuration

The script reads all settings from a `config.json` file in the same directory as the script. No command-line arguments — just run `python pdf_to_markdown.py`.

```json
{
    "source_files": "/Users/nathanaday/Documents/USC/EE450/Content/PDF Reading Excerpts/*.pdf",
    "output_files": "/Users/nathanaday/Documents/USC/EE450/Content/Converted Reading Excerpts/",
    "max_limit": 40
}
```

- `source_files` (required): a glob pattern pointing to the PDF files to process (supports `*` wildcards)
- `output_files` (required): path to the output directory for markdown files (create it if it doesn't exist)
- `max_limit` (required): maximum number of PDFs to process in a single run — acts as a safety cap to control API costs. If the glob matches more files than this limit, process only the first N (sorted alphabetically), print a warning that the limit was reached, and report how many were skipped

## Prompt to Send with Each PDF

Use this as the user message sent alongside each PDF document:

```
Convert this PDF to well-structured Markdown. This is a textbook chapter excerpt that will be processed downstream for topic pattern analysis, so completeness and structural accuracy matter more than visual formatting.

Guidelines:
- Preserve the full hierarchy of headings (chapter titles as #, sections as ##, subsections as ###, etc.)
- Capture ALL body text — do not summarize or omit anything
- Preserve numbered/bulleted lists as-is
- Convert tables to Markdown tables where possible; if a table is too complex, represent it as clearly as you can
- For figures/diagrams, insert a placeholder like [Figure: <caption or brief description>] — do not skip them silently
- Preserve bold/italic emphasis where it appears meaningful (e.g., key terms, definitions)
- Keep footnotes or endnotes as inline parentheticals or a notes section at the end
- Do not add any commentary, interpretation, or content that isn't in the source PDF
- If the PDF has page numbers, headers, or footers, omit those
- Output ONLY the Markdown content — no preamble, no code fences, no explanation
```

## API Call Structure

Each API call should:

1. Read the PDF file as bytes and base64-encode it
2. Send a single message with two content blocks:
   - A `document` block with `type: "base64"`, `media_type: "application/pdf"`, and the base64 data
   - A `text` block with the prompt above
3. Set `max_tokens` to 8192 (increase if your PDFs are very long — up to 16384 for dense chapters)
4. Extract the text content from the response and write it to the output `.md` file

## Dependencies

- `anthropic` (Anthropic Python SDK)
- Standard library only otherwise (`base64`, `pathlib`, `glob`, `json`, `sys`)

Install with: `pip install anthropic`

## Edge Cases to Handle

- Validate that `config.json` exists and contains all required keys; exit with a clear error if not
- Skip non-PDF files matched by the glob silently
- Warn if the glob matches zero PDFs
- If matched PDFs exceed `max_limit`, warn and report how many were skipped
- Skip PDFs that already have a corresponding `.md` file in the output directory (avoid reprocessing) — print a note when skipping
- Handle PDFs that are too large for the context window (catch the API error, log it, continue)
- Create the output directory if it doesn't exist

## Example Output

```
Loaded config.json
Source pattern: /Users/.../PDF Reading Excerpts/*.pdf
Output directory: /Users/.../Converted Reading Excerpts/
Max limit: 40

Found 47 PDFs matching pattern (capped at 40, skipping 7)

[1/40]  chapter_01.pdf ✓
[2/40]  chapter_02.pdf — skipped (already converted)
[3/40]  chapter_03.pdf ✗ (API error: context window exceeded)
[4/40]  chapter_04.pdf ✓
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total PDFs matched:   47
Limit applied:        40
Already converted:    3
Successful:           35
Failed:               2

Failed files:
  - chapter_03.pdf: API error: context window exceeded
  - chapter_29.pdf: File read error: permission denied
```
