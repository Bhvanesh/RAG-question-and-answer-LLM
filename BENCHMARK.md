# Benchmark — AI Document Q&A API with Hybrid RAG Search

Evaluation of retrieval configurations against a fixed 12-question
golden dataset derived from a real resume PDF document.

---

## Methodology

### Test Document
Surya Balakrishnan — Resume PDF (real document)

All questions were hand-crafted to cover different sections of the
document: skills, experience, education, certifications, and projects.
Ground truth answers were manually verified against the source document.

### Evaluation Metrics

Four RAGAS metrics measured per configuration:

```
Faithfulness:
→ LLM-as-judge: is every claim in the answer supported
  by the retrieved context?
→ 1.0 = fully grounded, 0.0 = hallucinated

Answer Relevancy:
→ cosine similarity between answer embedding and question embedding
→ 1.0 = answer directly addresses the question
→ 0.0 = answer went off-topic

Context Precision:
→ were the retrieved chunks actually useful?
→ 1.0 = all retrieved chunks were relevant
→ 0.5 = half the chunks were noise

Context Recall:
→ did retrieval find ALL the relevant information?
→ requires ground_truth to compute
→ 1.0 = everything needed was retrieved
→ 0.5 = missed half the relevant content
```

### Configurations Tested

```
Config 1: k=3, chunk=1000 (baseline)
→ vector search only, top 3 chunks, 1000 char chunks

Config 2: k=5, chunk=1000
→ vector search only, top 5 chunks, 1000 char chunks

Config 3: k=3, chunk=500
→ vector search only, top 3 chunks, 500 char chunks

Config 4: BM25 + vector + RRF (current production)
→ hybrid search, k=10 candidates each, RRF top 3
```

### Reproducibility

All evaluations run against the same 12-question golden dataset.
RAGAS uses GPT-4o-mini as judge — minor variation between runs
is expected. Results reflect a single representative run per config.

---

## Golden Dataset — 12 Questions

| # | Question | Type |
|---|----------|------|
| 1 | What is the candidate's CGPA? | Education |
| 2 | What degree does the candidate hold? | Education |
| 3 | Which company does the candidate currently work for? | Experience |
| 4 | What is the candidate's current job title? | Experience |
| 5 | Which university did the candidate attend? | Education |
| 6 | What cloud certification does the candidate hold? | Certifications |
| 7 | What programming languages does the candidate know? | Skills |
| 8 | What AI frameworks has the candidate worked with? | Skills |
| 9 | What databases has the candidate used? | Skills |
| 10 | When did the candidate start working at Accenture? | Experience |
| 11 | Which location is the candidate working in? | Personal |
| 12 | What is the candidate's location? | Personal |

Questions were designed to cover diverse document sections and
retrieval difficulty levels — from simple facts (CGPA) to
multi-context answers (AI frameworks across multiple bullets).

---

## Results

### Config 1 — k=3, chunk=1000 (Baseline)

```
Vector search only — top 3 chunks — 1000 character chunks
```

| Metric | Score |
|--------|-------|
| Faithfulness | 0.85 |
| Answer Relevancy | 0.96 |
| Context Precision | 0.889 |
| Context Recall | 0.917 |
| Failed questions | 0/12 |

**Notes:**
Solid baseline. High precision (0.889) — retrieved chunks were
relevant. Minor recall gap (0.917) — one or two questions missed
peripheral context. Faithfulness 0.85 suggests occasional minor
hallucination when context was incomplete.

---

### Config 2 — k=5, chunk=1000

```
Vector search only — top 5 chunks — 1000 character chunks
```

| Metric | Score | vs Baseline |
|--------|-------|-------------|
| Faithfulness | 0.66 | -22.4% |
| Answer Relevancy | 0.955 | -0.5% |
| Context Precision | 0.851 | -4.3% |
| Context Recall | 0.75 | -18.3% |
| Failed questions | 0/12 | — |

**Notes:**
Increasing k from 3 to 5 degraded all metrics. More chunks meant
more noise in the context window — the LLM became less precise
about which information to use. Faithfulness dropped 22% — a clear
sign that extra context introduces confusion rather than helping.
Recall also dropped unexpectedly — the LLM mixed information from
irrelevant chunks, reducing answer accuracy.

**Finding:** More retrieval is NOT always better. Context noise
hurts faithfulness significantly.

---

### Config 3 — k=3, chunk=500

```
Vector search only — top 3 chunks — 500 character chunks
```

| Metric | Score | vs Baseline |
|--------|-------|-------------|
| Faithfulness | 0.80 | -5.9% |
| Answer Relevancy | 0.96 | 0.0% |
| Context Precision | 0.816 | -8.2% |
| Context Recall | 0.75 | -18.3% |
| Failed questions | 0/12 | — |

**Notes:**
Halving chunk size degraded recall 18.3% — smaller chunks fragment
context across more pieces, so the top 3 retrieve less total
information. Precision also dropped — smaller chunks are less
self-contained, reducing per-chunk relevance. Relevancy held
steady since the question-answer alignment is independent of
chunk size.

**Finding:** Smaller chunks without increasing k hurts recall.
The information is still in the document but fragmented across
more chunks than k=3 can retrieve.

---

### Config 4 — BM25 + Vector + RRF (Current Production)

```
Hybrid search — vector k=10 + BM25 k=10 — RRF top 3
```

| Metric | Score | vs Baseline |
|--------|-------|-------------|
| Faithfulness | **0.889** | **+4.6%** |
| Answer Relevancy | **0.981** | **+2.2%** |
| Context Precision | 0.833 | -6.3% |
| Context Recall | **1.0** | **+9.0%** |
| Failed questions | 0/12 | — |

**Notes:**
Hybrid search achieved perfect recall (1.0) — found all relevant
content across all 12 questions. Faithfulness and relevancy both
improved over baseline. Context precision dropped slightly — an
expected tradeoff when combining two retrieval methods. With a
larger candidate pool (20 chunks total), RRF must filter more
aggressively, occasionally including marginally relevant chunks
before filtering to top 3.

**Finding:** BM25 recovers queries where semantic search fails on
exact terms (e.g. "AZ-900", "ChromaDB", specific job titles).
RRF re-ranks to top 3 before the LLM sees any context — so the
noise from larger candidate pools doesn't reach the LLM.

---

## Summary Table

| Configuration | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|
| k=3, chunk=1000 (baseline) | 0.85 | 0.96 | 0.889 | 0.917 |
| k=5, chunk=1000 | 0.66 | 0.955 | 0.851 | 0.75 |
| k=3, chunk=500 | 0.80 | 0.96 | 0.816 | 0.75 |
| BM25 + vector + RRF (current) | **0.889** | **0.981** | 0.833 | **1.0** |

Bold = improved vs baseline.
Context precision (0.833) not bolded — it dropped vs baseline.

---

## Key Findings

**Finding 1 — More retrieval degrades faithfulness:**
k=5 dropped faithfulness 22% vs k=3. Extra chunks add noise the
LLM can't always filter. The sweet spot for this document was k=3
for pure vector search.

**Finding 2 — Smaller chunks hurt recall without increasing k:**
k=3, chunk=500 dropped recall 18% vs baseline. The information
exists in the document but gets fragmented. If using smaller chunks,
k must increase proportionally.

**Finding 3 — Hybrid search achieves perfect recall:**
BM25 + vector + RRF is the only configuration to achieve recall=1.0.
Semantic search alone missed some keyword-dependent queries — BM25
recovers these without hurting faithfulness.

**Finding 4 — Precision tradeoff is acceptable:**
Hybrid search dropped context precision from 0.889 to 0.833. This
is expected — a wider candidate pool includes more marginal chunks.
The gain in recall (0.917 → 1.0) outweighs the precision cost for
this use case.

**Finding 5 — Zero failed questions across all configs:**
All 12 questions returned answers in all configurations. The failure
rate metric would matter more with adversarial or out-of-scope
questions not present in this golden dataset.

---

## Why These Results Matter

```
Faithfulness = trust
→ 0.889 means 88.9% of answer claims are document-grounded
→ critical for any application where hallucination causes harm

Recall = coverage
→ 1.0 means the system never misses relevant content
→ critical when users expect comprehensive answers

The combination (faithfulness 0.889 + recall 1.0) means:
→ the system finds everything relevant
→ and stays grounded in what it finds
```

---

## Running the Evaluation

```bash
# Upload your document via /upload
# Note the document_id returned

# Run batch evaluation
POST /batch-evaluate
{
  "document_id": your_document_id
}
```

---

## Honest Limitations

```
1. Single document:
   Evaluated on one resume PDF.
   Results may differ for longer, denser, or
   multi-topic documents.

2. RAGAS variance:
   LLM-as-judge metrics vary slightly between runs.
   Scores reflect one representative run per config.

3. Context precision requires ground_truth:
   Context recall was computed with ground_truth provided.
   Context precision without ground_truth may differ.
```
