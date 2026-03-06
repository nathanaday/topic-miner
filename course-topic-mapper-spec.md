# Course Topic Mapper — Implementation Spec

## Overview

A map-reduce LLM pipeline that ingests an entire semester's course materials and produces a hierarchical topic map with source references and priority scoring. Designed for graduate-level CS exam preparation.

**Input:** A directory of course materials (markdown, text, transcripts, etc.)
**Output:** A canonical JSON topic tree where every node carries source references, importance signals, and a priority score. Optional derived renderers produce markdown or checklist views.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 0: INGEST                         │
│  Classify each file by material type, chunk if needed,      │
│  assign document IDs, record line numbers                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                PHASE 1: MAP (per-document)                   │
│  For each document, extract a local topic tree using a       │
│  material-type-specific system prompt. Each node includes    │
│  source references (doc ID, line range). Parallelizable.     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: REDUCE (pairwise merge)                │
│  Merge local trees into a single global tree. Deduplicate    │
│  semantically equivalent topics. Accumulate source refs.     │
│  Uses pairwise tournament-style merging.                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 3: ENRICH & PRIORITIZE                    │
│  Score each node by frequency, source type, and importance   │
│  signals. Produce canonical JSON output.                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Ingestion & Preprocessing

### Purpose
Prepare raw files for LLM processing. Classify material types, assign stable identifiers, and handle chunking for oversized documents.

### Material Type Classification

Each input file must be tagged with one of the following types, which determines the system prompt used in Phase 1:

| Type          | Description                              | Example Files                        |
|---------------|------------------------------------------|--------------------------------------|
| `lecture`     | Lecture slides, transcripts, recordings  | `week3_lecture.md`, `lec05_notes.md` |
| `textbook`    | Textbook chapters, reading assignments   | `chapter4_transport_layer.md`        |
| `homework`    | Problem sets, programming assignments    | `hw3_problems.md`, `pa2_spec.md`     |
| `exam`        | Past exams, practice exams, midterms     | `midterm_2023_fall.md`               |
| `discussion`  | Discussion section notes, recitation     | `disc04_notes.md`                    |
| `student`     | Personal notes taken by the student      | `my_notes_week5.md`                  |

**Classification strategy:** First, attempt rule-based classification using filename patterns and directory structure (e.g., files in `lectures/` are type `lecture`). If ambiguous, prompt the LLM with the first ~50 lines and ask it to classify. Provide a config file (`material_config.yaml`) where the user can manually specify or override types.

### Config File: `material_config.yaml`

```yaml
course_name: "EE450 Computer Networks"
semester: "Fall 2025"

# Override automatic classification
file_overrides:
  "week3_guest_lecture.md": "lecture"
  "review_sheet.md": "student"

# Directory-based classification rules
directory_rules:
  "lectures/": "lecture"
  "readings/": "textbook"
  "homework/": "homework"
  "exams/": "exam"
  "discussion/": "discussion"
  "notes/": "student"

# Optional: provide a syllabus or topic list as a seed
# This helps the LLM anchor its extraction
seed_topics: []  # e.g., ["DNS", "TCP", "UDP", "Routing", "HTTP"]
```

### Document ID and Line Indexing

Every input file gets a stable document ID (e.g., `doc_001`). Before sending to the LLM, prepend line numbers to the content:

```
[doc_007] week3_lecture.md (type: lecture)
---
1: Today we're going to talk about DNS
2: So DNS is the domain name system
3: and what it does is translate human-readable names
...
80: Now this is really important for the exam
81: You need to understand iterative vs recursive resolution
```

This line-numbered format is what the LLM sees, allowing it to reference exact ranges in its output.

### Chunking Strategy

If a document exceeds ~80% of the model's context window (after accounting for the system prompt and output space), split it into overlapping chunks:

- **Chunk size:** ~6000 lines or ~100k tokens (tunable)
- **Overlap:** 200 lines between consecutive chunks to avoid losing context at boundaries
- **Chunk IDs:** `doc_007_chunk_01`, `doc_007_chunk_02`, etc.
- **Important:** Each chunk retains the original document's line numbers (do not restart numbering)

Small documents should not be chunked. Most individual lectures and homeworks will fit in a single call.

---

## Phase 1: Map (Per-Document Extraction)

### Purpose
Process each document independently to extract a local topic tree with source references and importance signals.

### Output Schema (per document)

Each Phase 1 LLM call must return JSON conforming to this schema:

```json
{
  "document_id": "doc_007",
  "document_name": "week3_lecture.md",
  "material_type": "lecture",
  "topics": [
    {
      "topic": "Domain Name System (DNS)",
      "level": "concept",
      "subtopics": [
        {
          "topic": "DNS Resolution Methods",
          "level": "subtopic",
          "subtopics": [
            {
              "topic": "Iterative DNS Resolution",
              "level": "learning_outcome",
              "description": "In iterative resolution, the local name server contacts each authoritative server on behalf of the client. Only the local name server acts as a client.",
              "source_refs": [
                {
                  "doc_id": "doc_007",
                  "filename": "week3_lecture.md",
                  "material_type": "lecture",
                  "lines": [80, 120],
                  "quote_snippet": "You need to understand iterative vs recursive..."
                }
              ],
              "importance_signals": [
                {
                  "type": "instructor_emphasis",
                  "detail": "Professor explicitly said 'important for the exam'",
                  "source_doc_id": "doc_007",
                  "source_line": 80
                }
              ],
              "subtopics": []
            }
          ],
          "source_refs": [
            {
              "doc_id": "doc_007",
              "filename": "week3_lecture.md",
              "material_type": "lecture",
              "lines": [75, 140],
              "quote_snippet": "DNS resolution methods..."
            }
          ],
          "importance_signals": [],
          "description": "Different approaches to resolving domain names: iterative, recursive."
        }
      ],
      "source_refs": [
        {
          "doc_id": "doc_007",
          "filename": "week3_lecture.md",
          "material_type": "lecture",
          "lines": [50, 200],
          "quote_snippet": "Today we're going to talk about DNS..."
        }
      ],
      "importance_signals": [],
      "description": "The system that translates human-readable domain names to IP addresses."
    }
  ]
}
```

### Schema Notes

- **`level`**: One of `concept` (broadest, e.g. "DNS"), `subtopic` (mid-level, e.g. "DNS Resolution Methods"), or `learning_outcome` (specific testable fact/skill).
- **`source_refs`**: Array of references. Each contains the document ID, denormalized filename and material type (for display convenience), a line range `[start, end]`, and a short snippet for human verification. A single topic node can have multiple refs if the topic spans non-contiguous sections. The denormalized fields are injected by the preprocessor so they carry through merges without requiring registry lookups.
- **`importance_signals`**: Array of signals detected by the LLM. Types are defined per material type (see below).
- **`description`**: A 1-2 sentence summary of the topic in the LLM's own words. This helps the merge phase identify semantic duplicates.
- **Nesting depth**: Allow up to 4 levels, but typical depth is 3 (concept → subtopic → learning outcome). The LLM should not force depth — shallow topics are fine.

### Field Lifecycle Across Phases

Not all fields in the final output schema exist at every phase. This table clarifies when each field is introduced:

| Field              | Phase 1 (Map) | Phase 2 (Reduce) | Phase 3 (Enrich) |
|--------------------|---------------|-------------------|-------------------|
| `id`               | —             | —                 | ✅ Generated       |
| `topic`            | ✅ LLM output  | ✅ May be renamed  | ✅ Unchanged       |
| `level`            | ✅ LLM output  | ✅ May be adjusted | ✅ Unchanged       |
| `description`      | ✅ LLM output  | ✅ Best kept       | ✅ Unchanged       |
| `source_refs`      | ✅ LLM output  | ✅ Accumulated     | ✅ Unchanged       |
| `importance_signals`| ✅ LLM output | ✅ Accumulated     | ✅ Unchanged       |
| `subtopics`        | ✅ LLM output  | ✅ Merged          | ✅ Unchanged       |
| `priority_score`   | —             | —                 | ✅ Computed        |
| `priority_band`    | —             | —                 | ✅ Derived from score |
| `study_note`       | —             | —                 | ✅ LLM generated   |
| `mastery_checklist`| —             | —                 | ✅ LLM generated   |

The Phase 1 and Phase 2 intermediate JSON files use the same node structure but omit the Phase 3 fields. The `id` field is assigned deterministically after the tree is finalized (post-merge) to ensure stable hierarchical numbering.

### Material-Type-Specific System Prompts

Each material type gets its own system prompt that guides extraction behavior. Below are the core instructions for each. These all share a common preamble (the output schema, general instructions) and diverge in their type-specific section.

---

#### Common Preamble (included in all Phase 1 prompts)

```
You are a course content analyzer. Your job is to read a single course document and extract a hierarchical topic tree.

OUTPUT FORMAT: Respond with valid JSON only, conforming to the provided schema. No markdown, no commentary.

HIERARCHY RULES:
- Level 1 "concept": Broad topics that would appear on a course syllabus (e.g., "DNS", "TCP Congestion Control")
- Level 2 "subtopic": Meaningful subdivisions of a concept (e.g., "DNS Resolution Methods", "TCP Slow Start")
- Level 3 "learning_outcome": Specific testable facts, procedures, or distinctions (e.g., "In iterative resolution, only the local name server acts as client")
- Level 4 (optional): Use only when a learning outcome has meaningful sub-components

Do not fabricate topics not present in the document. Extract only what is discussed.
Do not over-fragment. If a topic is mentioned briefly in one sentence, it can be a single learning_outcome node without its own subtopic layer.

SOURCE REFERENCES: For every topic node, include the line range where the topic is primarily discussed. The quote_snippet should be a short phrase (under 15 words) from near the start of that section to help the user locate it.

IMPORTANCE SIGNALS: Flag anything that suggests a topic is high-priority for exam preparation. The types of signals to watch for are listed in the material-specific instructions below.
```

---

#### `lecture` — Lecture Slides / Transcripts

```
MATERIAL TYPE: Lecture transcript or slides.

This content is from a professor's lecture, which may be conversational and informal. Topics may be introduced gradually, revisited, or discussed tangentially.

EXTRACTION GUIDANCE:
- The professor may introduce a topic, digress, then return to it. Group all discussion of the same topic together under one node rather than creating duplicates.
- Watch for topic transitions signaled by phrases like "now let's talk about," "moving on to," "the next thing is."
- Lecture content often includes examples and analogies. These are NOT separate topics — they support the parent topic. Only extract the underlying concept, not the example itself.
- If the professor works through a problem or derivation, the topic is the technique or concept being demonstrated, not the specific problem.

IMPORTANCE SIGNALS TO DETECT:
- "instructor_emphasis": Phrases like "this is important," "you need to know this," "this will be on the exam," "pay attention to," "I cannot stress this enough," "remember this," or any explicit emphasis on exam relevance.
- "repetition": A topic the professor returns to multiple times or restates in different ways.
- "contrast_highlight": When the professor explicitly contrasts two concepts ("don't confuse X with Y," "the key difference is"), both concepts and their distinction are high-priority.
- "common_mistake": When the professor warns about common errors ("students always get this wrong," "a common misconception is").
```

---

#### `textbook` — Textbook Chapters / Readings

```
MATERIAL TYPE: Textbook or assigned reading.

This content is already well-structured with sections and subsections. Your job is to distill it, not just mirror its structure.

EXTRACTION GUIDANCE:
- Do NOT simply replicate the textbook's heading structure. Evaluate whether the textbook's sections represent genuinely distinct topics or are just organizational.
- Textbooks cover topics comprehensively. Focus on what is likely testable: definitions, key mechanisms, algorithms, distinctions between related concepts, and quantitative relationships.
- Formulas, theorems, and named algorithms are almost always learning outcomes.
- Skip purely motivational content ("In the early days of the internet...") unless it provides necessary context for understanding a concept.
- Figures and diagrams referenced in the text often illustrate key learning outcomes — extract the concept the figure illustrates.

IMPORTANCE SIGNALS TO DETECT:
- "definition": Formal definitions of terms or concepts.
- "named_algorithm": A specific named protocol, algorithm, or mechanism (e.g., "Dijkstra's algorithm", "TCP Reno").
- "key_distinction": Explicit comparisons between related concepts.
- "formula": Mathematical relationships or equations.
```

---

#### `homework` — Problem Sets / Assignments

```
MATERIAL TYPE: Homework or programming assignment.

Homework problems implicitly identify important topics — if the professor assigned a problem on it, it's likely testable.

EXTRACTION GUIDANCE:
- Each problem or sub-problem typically maps to one or more topics. Extract the CONCEPT being tested, not the problem itself.
  - Example: A problem that asks "compute the subnet mask for a /24 network" maps to the learning outcome "Subnet mask calculation for CIDR notation," under the subtopic "IP Subnetting," under the concept "IP Addressing."
- If a problem integrates multiple topics, create a node for each topic referenced.
- Programming assignments test implementation understanding. Extract the concepts the student must understand to complete the assignment.
- Look at problem difficulty and point values if available — higher-weighted problems signal more important topics.

IMPORTANCE SIGNALS TO DETECT:
- "assigned_problem": The mere existence of a homework problem on this topic (every topic extracted from a homework gets this signal).
- "multi_step_problem": Problems requiring synthesis of multiple concepts.
- "high_point_value": Problems worth disproportionately more points.
```

---

#### `exam` — Past Exams / Practice Exams

```
MATERIAL TYPE: Past exam or practice exam.

Past exam content is the single strongest signal of what is testable. Every topic extracted here should be treated as high-priority.

EXTRACTION GUIDANCE:
- Each exam question maps to one or more topics. Extract the concept being tested.
- Pay attention to question format: multiple choice questions often test fine distinctions; long-form questions test deeper understanding and multi-step reasoning.
- If the exam includes an answer key or solutions, extract not just the topic but the specific knowledge needed to answer correctly.
- Note which topics appear across MULTIPLE past exams (this will be detected in the merge phase, but flag if you see repetition within this document, e.g., "Question 3 is similar to Question 1").

IMPORTANCE SIGNALS TO DETECT:
- "exam_appearance": Every topic from a past exam gets this signal, tagged with the exam name and question number.
- "high_point_value": Questions worth many points.
- "recurring_exam_topic": If you can detect that a topic appeared on multiple exams within this document set.
```

---

#### `discussion` — Discussion Section / Recitation Notes

```
MATERIAL TYPE: Discussion section or recitation notes.

Discussion sections typically reinforce lecture material, clarify confusing topics, and work through additional examples.

EXTRACTION GUIDANCE:
- Discussion sections often focus on topics students found confusing. The fact that a topic was covered in discussion is itself an importance signal.
- Q&A format content: the student question identifies the confusing topic, the TA/instructor answer provides the learning outcome.
- Worked examples in discussion follow the same rule as lectures: extract the concept, not the specific problem.

IMPORTANCE SIGNALS TO DETECT:
- "discussion_reinforcement": Topic was covered again in discussion (implies it's tricky or important).
- "student_confusion": Evidence that students found this topic confusing (questions, clarifications requested).
- "ta_emphasis": TA or instructor explicitly marked something as important.
```

---

#### `student` — Personal Student Notes

```
MATERIAL TYPE: Student's personal notes.

These are the user's own notes, which reflect their personal understanding and what they deemed important enough to write down.

EXTRACTION GUIDANCE:
- Student notes may be fragmentary, use shorthand, or reference things without full context. Do your best to extract coherent topic nodes.
- Personal annotations like "REVIEW THIS," "don't understand," "???" are importance signals.
- If the student's notes reference specific lectures, readings, or homework problems, preserve those references in the source_refs.
- The student may have already organized their notes by topic — respect that structure where it makes sense.

IMPORTANCE SIGNALS TO DETECT:
- "self_flagged": Student explicitly marked something for review ("TODO", "REVIEW", "important", "???", "don't understand").
- "noted_by_student": The general signal that the student chose to write this down (lower weight than other signals, but nonzero).
```

---

## Phase 2: Reduce (Pairwise Merge)

### Purpose
Merge all per-document topic trees into a single unified tree. Deduplicate semantically equivalent topics and accumulate source references.

### Merge Strategy: Pairwise Tournament

```
doc_001_tree ─┐
              ├─ merged_A ─┐
doc_002_tree ─┘             │
                            ├─ merged_C ─┐
doc_003_tree ─┐             │            │
              ├─ merged_B ─┘             │
doc_004_tree ─┘                          ├─ merged_E (final tree)
                                         │
doc_005_tree ─┐                          │
              ├─ merged_D ──────────────┘
doc_006_tree ─┘
```

This approach keeps each merge call manageable. Each merge operates on two trees, not the whole corpus. Ordering should place related documents adjacent (e.g., merge lecture week 3 with lecture week 4, not with the final exam) to maximize overlap and produce cleaner intermediate trees.

### Merge Prompt

```
You are a topic tree merger. You will receive two topic trees (Tree A and Tree B) extracted from course materials. Your job is to produce a single unified tree.

MERGE RULES:
1. DEDUPLICATION: If both trees contain the same concept, subtopic, or learning outcome (even if worded differently), merge them into a single node. Use your judgment — "Iterative DNS Resolution" and "DNS Iterative Queries" are the same topic.
2. ACCUMULATE REFERENCES: When merging duplicate nodes, combine their source_refs arrays and importance_signals arrays. Do not discard any references.
3. PRESERVE HIERARCHY: If Tree A has a topic as a subtopic of "DNS" and Tree B has the same topic as a subtopic of "Networking Fundamentals," use your judgment about the most appropriate parent. Prefer the more specific, standard grouping.
4. CHOOSE THE BEST NAME: When merging equivalent topics with different names, choose the name that is most precise, standard, and descriptive.
5. KEEP THE BEST DESCRIPTION: When merging, keep whichever description is more complete and accurate, or synthesize a better one from both.
6. DO NOT DROP TOPICS: Every topic from both trees must appear in the output. If a topic from one tree has no counterpart in the other, include it as-is.
7. MAINTAIN LEVELS: Ensure the level field (concept/subtopic/learning_outcome) remains appropriate after merging. If a node was a "concept" in one tree and a "subtopic" in another, determine which is correct based on its scope.

OUTPUT: A single merged topic tree in the same JSON schema as the inputs.
```

### Pre-Merge Similarity Hint (Optional Optimization)

Before the LLM merge call, compute cosine similarity between topic names (using an embedding model) across the two trees. Include a hint section in the prompt:

```
LIKELY DUPLICATES (based on similarity analysis):
- Tree A: "TCP Slow Start" <-> Tree B: "Slow Start Algorithm" (similarity: 0.94)
- Tree A: "ARP Table" <-> Tree B: "ARP Cache" (similarity: 0.91)

Use your judgment — these are suggestions, not commands. Some may be false positives.
```

This reduces the LLM's search space and improves merge quality.

### Handling Large Trees

If the merged tree grows too large to fit in a single context window, split the merge into sub-tree merges by top-level concept. For example, merge all "DNS"-related subtrees separately from all "TCP"-related subtrees. This is safe because top-level concepts rarely need to be merged with each other.

---

## Phase 3: Enrich & Prioritize

### Purpose
Score every node in the final tree for exam importance and produce the final output formats.

### Scoring Algorithm

Each node receives a composite `priority_score` (0-100) computed from:

```
priority_score = (
    w1 * exam_appearance_score +      # Appeared on past exam(s)
    w2 * instructor_emphasis_score +   # Professor flagged it
    w3 * frequency_score +             # Appears in many documents
    w4 * homework_score +              # Was a homework topic
    w5 * discussion_score +            # Covered in discussion
    w6 * self_flagged_score +          # Student flagged for review
    w7 * depth_coverage_score          # Has many subtopics/outcomes
)
```

Suggested default weights (tunable in config):

| Signal                  | Weight | Rationale                                    |
|-------------------------|--------|----------------------------------------------|
| `exam_appearance`       | 30     | Strongest predictor of exam relevance        |
| `instructor_emphasis`   | 25     | Direct signal from the professor             |
| `homework_problem`      | 15     | Practiced topics are testable topics         |
| `frequency` (multi-doc) | 15     | Core topics appear everywhere                |
| `discussion_covered`    | 8      | Reinforced topics are tricky/important       |
| `self_flagged`          | 5      | Personal weak spots                          |
| `depth_coverage`        | 2      | More subtopics = more to study               |

Scores should propagate: a concept node's score is the max of its own score and its children's scores (so a concept with one very high-priority learning outcome bubbles up).

### Enrichment Prompt

```
You are a study prioritization assistant. You will receive a complete course topic tree with accumulated importance_signals and source_refs on each node.

For each node, compute a priority_score (0-100) using the following weights: [insert weights].

Also, for each concept-level node, generate:
- A 1-sentence "study_note" summarizing what the student should focus on
- A "mastery_checklist" of 2-5 concrete things the student should be able to do/explain to demonstrate mastery

Add these fields to each node and return the enriched tree.
```

---

## Final Output Format

### Canonical Output: JSON

The pipeline produces a single JSON file as its canonical output. This file contains the complete enriched topic tree and all metadata needed to power a visualization app, generate flashcards, track progress, or render any derived view (markdown, checklist, etc.). Markdown and other human-readable formats are optional derived renderers, not primary outputs.

### Why JSON (not YAML, not markdown)

- The entire pipeline already operates on JSON trees internally. The final output is just the last stage with zero transformation.
- YAML introduces implicit type coercion risks (e.g., `NO` becomes boolean `false`, bare numbers lose precision), multiline string ambiguity, and an additional parsing dependency — all for readability that a visualization app doesn't need.
- Markdown is lossy. You can render JSON to markdown trivially, but you cannot reliably parse structured data back out of markdown.
- JSON is natively consumable by React, Vue, or any frontend framework with zero parsing overhead.

### Complete Output Schema

The output file is a single JSON object with two top-level keys: `metadata` (about the pipeline run) and `topics` (the tree itself).

```json
{
  "metadata": {
    "course_name": "EE450 Computer Networks",
    "semester": "Fall 2025",
    "generated_at": "2025-11-15T03:22:00Z",
    "pipeline_version": "1.0.0",
    "document_registry": [
      {
        "doc_id": "doc_001",
        "filename": "week1_lecture.md",
        "material_type": "lecture",
        "total_lines": 340,
        "chunks": 1
      },
      {
        "doc_id": "doc_007",
        "filename": "week3_lecture.md",
        "material_type": "lecture",
        "total_lines": 520,
        "chunks": 1
      },
      {
        "doc_id": "doc_015",
        "filename": "midterm_2023_fall.md",
        "material_type": "exam",
        "total_lines": 180,
        "chunks": 1
      }
    ],
    "stats": {
      "total_documents": 20,
      "total_concepts": 12,
      "total_subtopics": 47,
      "total_learning_outcomes": 183,
      "total_nodes": 242
    }
  },
  "topics": [
    {
      "id": "topic_001",
      "topic": "Domain Name System (DNS)",
      "level": "concept",
      "description": "The system that translates human-readable domain names to IP addresses.",
      "priority_score": 92,
      "priority_band": "critical",
      "study_note": "Understand both resolution methods cold, and know all record types by function.",
      "mastery_checklist": [
        "Explain the difference between iterative and recursive DNS resolution",
        "List the four DNS record types and their purposes",
        "Trace a complete DNS lookup from browser to authoritative server"
      ],
      "source_refs": [
        {
          "doc_id": "doc_007",
          "filename": "week3_lecture.md",
          "material_type": "lecture",
          "lines": [50, 200],
          "quote_snippet": "Today we're going to talk about DNS"
        },
        {
          "doc_id": "doc_010",
          "filename": "chapter4_application_layer.md",
          "material_type": "textbook",
          "lines": [300, 450],
          "quote_snippet": "The Domain Name System is a distributed database"
        },
        {
          "doc_id": "doc_015",
          "filename": "midterm_2023_fall.md",
          "material_type": "exam",
          "lines": [45, 62],
          "quote_snippet": "Question 6: DNS resolution"
        }
      ],
      "importance_signals": [
        {
          "type": "instructor_emphasis",
          "detail": "Professor dedicated an entire lecture to DNS",
          "source_doc_id": "doc_007",
          "source_line": 50
        },
        {
          "type": "exam_appearance",
          "detail": "2023 Fall Midterm Question 6",
          "source_doc_id": "doc_015",
          "source_line": 45
        }
      ],
      "subtopics": [
        {
          "id": "topic_001_001",
          "topic": "DNS Resolution Methods",
          "level": "subtopic",
          "description": "The two approaches to resolving domain names: iterative and recursive.",
          "priority_score": 90,
          "priority_band": "critical",
          "study_note": null,
          "mastery_checklist": null,
          "source_refs": [
            {
              "doc_id": "doc_007",
              "filename": "week3_lecture.md",
              "material_type": "lecture",
              "lines": [75, 160],
              "quote_snippet": "There are two ways to resolve a name"
            }
          ],
          "importance_signals": [],
          "subtopics": [
            {
              "id": "topic_001_001_001",
              "topic": "Iterative DNS Resolution",
              "level": "learning_outcome",
              "description": "In iterative resolution, the local name server contacts each authoritative server on behalf of the client. Only the local name server acts as a client.",
              "priority_score": 95,
              "priority_band": "critical",
              "study_note": null,
              "mastery_checklist": null,
              "source_refs": [
                {
                  "doc_id": "doc_007",
                  "filename": "week3_lecture.md",
                  "material_type": "lecture",
                  "lines": [80, 120],
                  "quote_snippet": "In iterative mode, the local server does all the work"
                },
                {
                  "doc_id": "doc_010",
                  "filename": "chapter4_application_layer.md",
                  "material_type": "textbook",
                  "lines": [310, 340],
                  "quote_snippet": "Iterative queries place the burden on the local resolver"
                },
                {
                  "doc_id": "doc_015",
                  "filename": "midterm_2023_fall.md",
                  "material_type": "exam",
                  "lines": [45, 52],
                  "quote_snippet": "Q6a: Describe iterative resolution"
                }
              ],
              "importance_signals": [
                {
                  "type": "instructor_emphasis",
                  "detail": "Professor said 'you need to understand iterative vs recursive for the exam'",
                  "source_doc_id": "doc_007",
                  "source_line": 80
                },
                {
                  "type": "exam_appearance",
                  "detail": "2023 Fall Midterm Q6a",
                  "source_doc_id": "doc_015",
                  "source_line": 45
                },
                {
                  "type": "assigned_problem",
                  "detail": "Homework 3 Problem 2",
                  "source_doc_id": "doc_012",
                  "source_line": 15
                }
              ],
              "subtopics": []
            },
            {
              "id": "topic_001_001_002",
              "topic": "Recursive DNS Resolution",
              "level": "learning_outcome",
              "description": "In recursive resolution, each server in the chain contacts the next server and passes the final result back through the chain.",
              "priority_score": 88,
              "priority_band": "critical",
              "study_note": null,
              "mastery_checklist": null,
              "source_refs": [
                {
                  "doc_id": "doc_007",
                  "filename": "week3_lecture.md",
                  "material_type": "lecture",
                  "lines": [121, 155],
                  "quote_snippet": "In recursive mode, each server asks the next"
                }
              ],
              "importance_signals": [
                {
                  "type": "contrast_highlight",
                  "detail": "Explicitly contrasted with iterative resolution",
                  "source_doc_id": "doc_007",
                  "source_line": 125
                }
              ],
              "subtopics": []
            }
          ]
        }
      ]
    }
  ]
}
```

### Schema Field Reference

#### `metadata` (top-level)

| Field               | Type     | Description                                                                                   |
|---------------------|----------|-----------------------------------------------------------------------------------------------|
| `course_name`       | string   | Name of the course, from config                                                              |
| `semester`          | string   | Semester identifier, from config                                                             |
| `generated_at`      | string   | ISO 8601 timestamp of pipeline run                                                           |
| `pipeline_version`  | string   | Semver of the tool that generated this file                                                  |
| `document_registry` | array    | Every input document with its ID, filename, type, and size. This is the lookup table for resolving `doc_id` references throughout the tree. |
| `stats`             | object   | Summary counts for quick display (total nodes, concepts, subtopics, learning outcomes)       |

#### Topic Node (recursive, used at every level of the tree)

| Field                | Type          | Description                                                                                       |
|----------------------|---------------|---------------------------------------------------------------------------------------------------|
| `id`                 | string        | Stable unique ID using hierarchical numbering (e.g., `topic_003_002_001`). Enables deep-linking in a future UI. |
| `topic`              | string        | Human-readable topic name                                                                         |
| `level`              | enum          | One of: `concept`, `subtopic`, `learning_outcome`. Determines display behavior in a UI.          |
| `description`        | string        | 1-2 sentence summary in the LLM's own words. Used for semantic deduplication in Phase 2 and for display in a UI. |
| `priority_score`     | integer 0-100 | Composite importance score computed in Phase 3                                                    |
| `priority_band`      | enum          | One of: `critical` (80-100), `important` (50-79), `moderate` (20-49), `low` (0-19). Derived from score for easy filtering/coloring. |
| `study_note`         | string\|null  | 1-sentence focus guidance. Generated only for `concept`-level nodes.                              |
| `mastery_checklist`  | array\|null   | 2-5 concrete "can you do this?" items. Generated only for `concept`-level nodes.                  |
| `source_refs`        | array         | All source references for this node (accumulated across merges). See Source Ref schema below.     |
| `importance_signals` | array         | All detected importance signals (accumulated across merges). See Importance Signal schema below.  |
| `subtopics`          | array         | Child topic nodes. Empty array `[]` for leaf nodes.                                               |

#### Source Reference

| Field           | Type   | Description                                                                                 |
|-----------------|--------|---------------------------------------------------------------------------------------------|
| `doc_id`        | string | References an entry in `metadata.document_registry`                                         |
| `filename`      | string | Denormalized filename for display convenience (avoids requiring a registry lookup in the UI) |
| `material_type` | string | Denormalized material type for display/filtering                                            |
| `lines`         | [int, int] | Inclusive line range `[start, end]` in the original document                             |
| `quote_snippet` | string | Short phrase (under 15 words) from near the start of the referenced section, for human verification and preview |

#### Importance Signal

| Field           | Type   | Description                                                      |
|-----------------|--------|------------------------------------------------------------------|
| `type`          | string | Signal category (see material-type-specific prompts for full list: `instructor_emphasis`, `exam_appearance`, `assigned_problem`, `repetition`, `contrast_highlight`, `common_mistake`, `definition`, `named_algorithm`, `key_distinction`, `formula`, `discussion_reinforcement`, `student_confusion`, `self_flagged`, etc.) |
| `detail`        | string | Human-readable explanation of the signal                         |
| `source_doc_id` | string | Which document this signal was detected in                       |
| `source_line`   | int    | Approximate line where the signal was detected                   |

### Design Decisions for Frontend Compatibility

Several schema choices are made specifically to support a future visualization app:

- **Hierarchical IDs** (`topic_003_002_001`) let the UI construct breadcrumbs and deep-link URLs trivially (e.g., `/topic/003/002/001`).
- **`priority_band`** is pre-computed so the frontend can color-code nodes without reimplementing the banding logic.
- **Denormalized `filename` and `material_type` in source refs** means the UI can render a source reference without a separate lookup into the document registry. The registry still exists for when you need full document metadata.
- **`study_note` and `mastery_checklist` only on concept nodes** keeps the schema clean — leaf nodes carry raw knowledge, parent nodes carry study strategy.
- **Empty `subtopics: []` on leaves** (rather than omitting the field) means the UI can always iterate over `node.subtopics` without null-checking.

### Optional Derived Outputs

The pipeline can optionally render derived views from the canonical JSON. These are convenience outputs, not primary artifacts:

- **Markdown topic map:** A nested markdown rendering with priority indicators and source references. Useful for quick review in a text editor or printing.
- **Flat checklist:** A priority-sorted list of all learning outcomes with mastery questions. Useful for final pre-exam triage.

These renderers read the JSON and produce their output deterministically — no LLM calls required. They live in `src/output/` and are invoked via CLI flags (`--render markdown`, `--render checklist`).

---

## Technical Implementation Notes

### LLM Configuration

- **Model:** Claude Sonnet 4 (`claude-sonnet-4-20250514`) for Phase 1 (map) and Phase 3 (enrich). These are high-volume, somewhat routine extraction tasks.
- **Model:** Claude Sonnet 4 for Phase 2 (reduce) as well, though if merge quality is insufficient, escalate to a stronger model for merge calls.
- **Temperature:** 0 for all calls. This is a factual extraction task.
- **Max tokens:** 8192 for Phase 1 (individual documents), 16384 for Phase 2 (merged trees can be large).
- **Structured output:** Use Anthropic's JSON mode / tool-use to enforce schema compliance.

### Parallelism

Phase 1 is embarrassingly parallel. All documents can be processed simultaneously (subject to API rate limits). Use a concurrency pool of ~10 parallel requests.

Phase 2 must respect the tournament bracket dependency structure, but independent branches can run in parallel.

### Error Handling

- If a Phase 1 call fails or returns malformed JSON, retry up to 3 times with the same input.
- If a merge call produces a tree that is missing topics from either input (detected via a set-difference check on topic names), re-run the merge with an explicit warning: "Your previous merge dropped the following topics: [list]. Ensure all topics appear in the output."
- Log every LLM call's input/output for debugging.

---

## Future Extensions (Out of Scope for V1)

- **Interactive web UI:** Render the topic tree as a collapsible, searchable web app with progress tracking (checkboxes that persist).
- **Flashcard generation:** For each learning outcome, auto-generate Anki-compatible flashcards.
- **Gap detection:** Compare the topic map against a provided syllabus or learning objectives list to detect topics that weren't well-covered in the materials.
- **Incremental updates:** When a new document is added (e.g., a new lecture), run Phase 1 on just that document and merge it into the existing tree without reprocessing everything.
- **Multi-format input:** Support PDF slides, PPTX files, and audio transcripts (via Whisper) in addition to markdown/text.
