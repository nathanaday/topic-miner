# Topic Miner

A map-reduce LLM pipeline that mines topics from a variety of course materials, eventually producing a single, consolidated topic map.

## Background

Course materials are scattered across dozens of files -- lecture transcripts, textbook chapters, homework sets, past exams, discussion notes, personal notes -- each covering overlapping topics in different formats and levels of detail. Manually cross-referencing all of these to figure out *what matters most* is tedious and error-prone, especially under time pressure before an exam. A topic can always slip through the cracks when studying, and only in hindsight does the student realize it was burried in a lecture note.

#### Map Reduce Design with LLM

```
                    INGEST
                      |
          classify, line-number, chunk
                      |
                     MAP
                      |
        one LLM call per document, in parallel
        each produces a local topic tree with
        source references and importance signals
                      |
                    REDUCE
                      |
        pairwise tournament merging of trees
        deduplicate semantically equivalent topics
        accumulate all source references
                      |
                    ENRICH
                      |
        score every node by exam relevance
        add study notes and mastery checklists
                      |
              topic_map.json
```

**Map** -- Each document is processed independently with a material-type-specific prompt. A lecture transcript prompt knows to watch for instructor emphasis ("this will be on the exam"); a homework prompt treats every problem as an importance signal; a past exam prompt treats everything as high-priority. Each call returns a structured topic tree with line-level source references.

**Reduce** -- Local trees are merged pairwise in a tournament bracket. The LLM deduplicates semantically equivalent topics (e.g., "TCP Slow Start" and "Slow Start Algorithm"), chooses the best name and description, and accumulates all source references. After log2(n) rounds, a single unified tree remains.

**Enrich** -- The final tree is scored. Each node gets a composite priority score (0-100) based on weighted signals: past exam appearances, instructor emphasis, homework coverage, cross-document frequency, discussion reinforcement, and student self-flags. Concept-level nodes get study notes and mastery checklists.

### Advantages

No single LLM call can process an entire course at once -- the combined materials exceed any context window. But even if they could fit, a monolithic call would produce worse results. The map-reduce structure provides:

- Adding more documents adds more map calls, not more complexity per call.
- All map calls are independent and run concurrently.
- A failed call only affects one document. Completed maps are checkpointed to disk and skipped on retry.
- Every topic node carries source references back to exact line ranges in the original material, surviving through all merges.


### Drawbacks

The full topic map does not fit into any LLM context window, so the merge and enrichment phase is prone to duplicating topic trees and not detecting that they have been duplicated. Creating an intelligent merge stage is the clearest next improvement.

---

## Visualization Interface

This repository has a built in visualizer! Run it locally on the results of your topic map, and track your mastery of each topic.

>[!TIP] See the `/interaction` directory for details
>https://github.com/nathanaday/topic-miner/tree/main/interaction

<img width="1840" height="1114" alt="Screenshot 2026-03-07 at 10 52 53 AM" src="https://github.com/user-attachments/assets/3015720b-8665-447e-b858-bca300abe93e" />



---

## Usage

>[!WARNING] API usage costs
> Until I find more opportunities to save context at the MAP and MERGE steps, this is a very LLM intensive process. Thousands of pages of documents will be continuously analyzed and merged. The total API cost is on the order of $20-40 for a large course. Test on very small batches first before comitting to the entire course repo.


```bash
# Set up
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Run
python run.py path/to/course/materials/

# With optional rendered views
python run.py path/to/course/materials/ --render markdown checklist
```

## Output

The pipeline produces `topic_map.json` -- a single canonical JSON file containing the complete enriched topic tree with metadata, a document registry, source references, importance signals, priority scores, and study guidance. Optional renderers produce markdown and checklist views.

## Configuration

Edit `material_config.yaml` to set course name, directory-to-material-type mappings, scoring weights, and LLM parameters.


### Known Issues

The topic_map.json contains duplicate subtopic IDs (same node appears under multiple parents). Only 1158 of 4149 nodes have unique IDs. 80% of links (3270/4099) target duplicate IDs

On analysis, the issue is related to multiple merge stages duplicating entire trees under one parent, instead of merging them. For now, after a topic mining execution, run the script `tools/TopicMapAnalysis/dedup_topic_map.py`, which will procedurally merge duplicate topic ideas and combine until no duplicates remain. There is not yet an automated solution to doing this in the merge/enrich phases but I'll look into it.
